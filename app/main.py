from pathlib import Path
import uuid
import sqlite3
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db, save_document, get_documents, DB_PATH
from app.services.document_parser import extract_document, combine_pages
from app.services.legal_analyzer import classify_document, extract_key_information, detect_clauses
from app.services.summarizer import summarize
from app.services.qa_engine import answer_question

BASE = Path(__file__).resolve().parent.parent
UPLOADS = BASE / "uploads"
UPLOADS.mkdir(exist_ok=True)

app = FastAPI(title="Legal Document Summariser")
app.mount("/static", StaticFiles(directory=str(BASE / "app" / "static")), name="static")
init_db()

@app.get("/")
def home():
    return FileResponse(BASE / "app" / "static" / "index.html")

@app.get("/api/history")
def history():
    return get_documents()

@app.post("/api/summarize")
async def summarize_document(file: UploadFile = File(...), level: str = Form("medium")):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(400, "Only PDF, DOCX and TXT files are supported.")

    path = UPLOADS / f"{uuid.uuid4().hex}{suffix}"
    path.write_bytes(await file.read())

    try:
        pages = extract_document(str(path))
        text = combine_pages(pages)
        if len(text.strip()) < 50:
            raise HTTPException(422, "Very little text was extracted. The PDF may be scanned and require OCR.")

        doc_type = classify_document(text)
        summary = summarize(text, level)
        info = extract_key_information(text)
        clauses = detect_clauses(text)
        doc_id = save_document(file.filename, doc_type, summary)

        return {
            "document_id": str(doc_id),
            "filename": file.filename,
            "document_type": doc_type,
            "summary": summary,
            "key_information": info,
            "clauses": clauses,
            "pages": len(pages),
            "raw_text": text
        }
    finally:
        path.unlink(missing_ok=True)

@app.post("/api/ask")
async def ask(question: str = Form(...), text: str = Form(...)):
    pages = []
    for block in text.split("\n\n"):
        if block.startswith("[PAGE "):
            first, *rest = block.split("\n")
            try:
                number = int(first.replace("[PAGE ", "").replace("]", ""))
            except ValueError:
                number = 1
            pages.append({"page": number, "text": "\n".join(rest)})
    if not pages:
        pages = [{"page": 1, "text": text}]
    return answer_question(question, pages)

@app.get("/api/download/{doc_id}")
def download(doc_id: int):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT filename, document_type, summary FROM documents WHERE id=?", (doc_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Document not found.")

    filename, doc_type, summary = row
    out = UPLOADS / f"summary_{doc_id}.txt"
    out.write_text(
        f"LEGAL DOCUMENT SUMMARY\n\nOriginal File: {filename}\nDocument Type: {doc_type}\n\n"
        f"SUMMARY\n{'-'*60}\n{summary}\n\n"
        "DISCLAIMER\nThis AI-generated summary is for educational/informational use only and is not legal advice.\n",
        encoding="utf-8"
    )
    return FileResponse(out, media_type="text/plain", filename=f"{Path(filename).stem}_summary.txt")

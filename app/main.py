from pathlib import Path
import uuid
import sqlite3

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db, save_document, get_documents, DB_PATH
from app.services.document_parser import extract_document, combine_pages
from app.services.legal_analyzer import (
    classify_document,
    extract_key_information,
    detect_clauses,
)
from app.services.summarizer import summarize
from app.services.qa_engine import answer_question


BASE = Path(__file__).resolve().parent.parent
UPLOADS = BASE / "uploads"

UPLOADS.mkdir(exist_ok=True)

app = FastAPI(
    title="Legal Document Summariser",
    description="AI-assisted Legal Document Summarisation System",
    version="1.0.0",
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE / "app" / "static")),
    name="static",
)

init_db()


@app.get("/")
def home():
    return FileResponse(
        BASE / "app" / "static" / "index.html"
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "message": "Legal Document Summariser API is running"
    }


@app.get("/api/history")
def history():
    return get_documents()


@app.post("/api/summarize")
async def summarize_document(
    file: UploadFile = File(...),
    level: str = Form("medium"),
):

    try:

        # Check file
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No file selected."
            )

        suffix = Path(file.filename).suffix.lower()

        allowed_extensions = {
            ".pdf",
            ".docx",
            ".txt"
        }

        if suffix not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail="Only PDF, DOCX and TXT files are supported."
            )

        # Validate summary level
        if level not in {"short", "medium", "long"}:
            level = "medium"

        # Save temporary file
        temporary_filename = f"{uuid.uuid4().hex}{suffix}"
        file_path = UPLOADS / temporary_filename

        file_data = await file.read()

        if not file_data:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        file_path.write_bytes(file_data)

        try:

            # -------------------------------
            # TEXT EXTRACTION
            # -------------------------------

            pages = extract_document(
                str(file_path)
            )

            text = combine_pages(pages)

            if not text or len(text.strip()) < 50:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Very little text was extracted from the document. "
                        "If this is a scanned PDF, OCR is required."
                    )
                )

            # -------------------------------
            # DOCUMENT CLASSIFICATION
            # -------------------------------

            document_type = classify_document(
                text
            )

            # -------------------------------
            # SUMMARY
            # -------------------------------

            summary = summarize(
                text,
                level
            )

            # -------------------------------
            # KEY INFORMATION
            # -------------------------------

            key_information = extract_key_information(
                text
            )

            # -------------------------------
            # CLAUSES
            # -------------------------------

            clauses = detect_clauses(
                text
            )

            # -------------------------------
            # DATABASE
            # -------------------------------

            document_id = save_document(
                file.filename,
                document_type,
                summary
            )

            # -------------------------------
            # RESPONSE
            # -------------------------------

            return {
                "success": True,
                "document_id": str(document_id),
                "filename": file.filename,
                "document_type": document_type,
                "summary": summary,
                "key_information": key_information,
                "clauses": clauses,
                "pages": len(pages),
                "raw_text": text,
            }

        finally:

            # Delete temporary uploaded file
            try:
                file_path.unlink(
                    missing_ok=True
                )
            except Exception:
                pass

    except HTTPException:
        raise

    except Exception as error:

        print("\n==============================")
        print("SUMMARIZATION ERROR")
        print("==============================")
        print(type(error).__name__)
        print(str(error))
        print("==============================\n")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": type(error).__name__,
                "detail": str(error),
            }
        )


@app.post("/api/ask")
async def ask_question(
    question: str = Form(...),
    text: str = Form(...)
):

    try:

        if not question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty."
            )

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Document text is empty."
            )

        pages = []

        blocks = text.split("\n\n")

        for block in blocks:

            if block.startswith("[PAGE "):

                first_line, *remaining = block.split("\n")

                try:
                    page_number = int(
                        first_line
                        .replace("[PAGE ", "")
                        .replace("]", "")
                    )
                except ValueError:
                    page_number = 1

                page_text = "\n".join(
                    remaining
                )

                pages.append({
                    "page": page_number,
                    "text": page_text
                })

        if not pages:

            pages = [
                {
                    "page": 1,
                    "text": text
                }
            ]

        result = answer_question(
            question,
            pages
        )

        return {
            "success": True,
            **result
        }

    except HTTPException:
        raise

    except Exception as error:

        print("\n==============================")
        print("QUESTION ANSWERING ERROR")
        print("==============================")
        print(type(error).__name__)
        print(str(error))
        print("==============================\n")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": type(error).__name__,
                "detail": str(error),
            }
        )


@app.get("/api/download/{doc_id}")
def download_summary(
    doc_id: int
):

    conn = sqlite3.connect(
        DB_PATH
    )

    row = conn.execute(
        """
        SELECT filename, document_type, summary
        FROM documents
        WHERE id = ?
        """,
        (doc_id,)
    ).fetchone()

    conn.close()

    if not row:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    filename, document_type, summary = row

    output_file = (
        UPLOADS /
        f"summary_{doc_id}.txt"
    )

    output_file.write_text(
        f"""
LEGAL DOCUMENT SUMMARY
========================================

Original File:
{filename}

Document Type:
{document_type}

SUMMARY
========================================

{summary}


DISCLAIMER
========================================

This AI-generated summary is provided for
educational and informational purposes only.

It does not constitute legal advice.

Consult a qualified legal professional for
legal decisions.
""",
        encoding="utf-8"
    )

    return FileResponse(
        output_file,
        media_type="text/plain",
        filename=f"{Path(filename).stem}_summary.txt"
    )
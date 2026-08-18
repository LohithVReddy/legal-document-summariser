from pathlib import Path
import re
import fitz
from docx import Document

def clean_text(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \\t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_document(path):
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        doc = fitz.open(path)
        pages = []
        for i, page in enumerate(doc):
            pages.append({"page": i + 1, "text": clean_text(page.get_text("text"))})
        doc.close()
        return pages
    if ext == ".docx":
        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return [{"page": 1, "text": clean_text(text)}]
    if ext == ".txt":
        return [{"page": 1, "text": clean_text(Path(path).read_text(encoding="utf-8", errors="ignore"))}]
    raise ValueError("Only PDF, DOCX and TXT files are supported.")

def combine_pages(pages):
    return "\n\n".join(
        f"[PAGE {p['page']}]\n{p['text']}" for p in pages if p["text"]
    )

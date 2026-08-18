import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "legal_summariser.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            document_type TEXT,
            summary TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_document(filename, document_type, summary):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "INSERT INTO documents(filename, document_type, summary) VALUES (?, ?, ?)",
        (filename, document_type, summary)
    )
    conn.commit()
    doc_id = cur.lastrowid
    conn.close()
    return doc_id

def get_documents():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, filename, document_type, uploaded_at FROM documents ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

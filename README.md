# Legal Document Summariser

Final-year CSE project: upload PDF/DOCX/TXT legal documents, extract text, classify the document, generate an extractive NLP summary, detect common legal clauses/entities, and ask questions with source-page references.

## Run in VS Code

1. Install Python 3.10+
2. Open this folder in VS Code.
3. Create and activate a virtual environment:
   `python -m venv venv`
4. Windows:
   `venv\Scripts\activate`
5. Install:
   `pip install -r requirements.txt`
6. Start:
   `uvicorn app.main:app --reload`
7. Open http://127.0.0.1:8000

Supported: PDF, DOCX, TXT.

This is an educational prototype and does not provide legal advice.

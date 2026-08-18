import re

PATTERNS = {
    "Court Judgment": ["judgment", "petitioner", "respondent", "bench", "appeal"],
    "Contract / Agreement": ["agreement", "party", "parties", "consideration", "termination"],
    "Employment Agreement": ["employer", "employee", "salary", "employment", "probation"],
    "Lease / Rental Agreement": ["landlord", "tenant", "rent", "lease", "premises"],
    "Legal Notice": ["legal notice", "demand", "notice", "hereby"],
    "Non-Disclosure Agreement": ["confidential information", "non-disclosure", "nda", "confidentiality"],
    "Terms and Conditions": ["terms and conditions", "privacy", "service", "user"]
}

CLAUSES = {
    "Termination Clause": ["termination", "terminate"],
    "Confidentiality Clause": ["confidentiality", "confidential information", "non-disclosure"],
    "Payment Clause": ["payment", "fee", "fees", "invoice", "compensation"],
    "Liability Clause": ["liability", "liable", "damages", "indemnity"],
    "Jurisdiction Clause": ["jurisdiction", "governing law", "courts at"],
    "Dispute Resolution Clause": ["arbitration", "dispute resolution", "mediation"],
    "Intellectual Property Clause": ["intellectual property", "copyright", "trademark", "ownership"]
}

def classify_document(text):
    low = text.lower()
    scores = {name: sum(word in low for word in words) for name, words in PATTERNS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "General Legal Document"

def extract_key_information(text):
    dates = re.findall(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b", text, re.I)
    money = re.findall(r"(?:₹|Rs\.?|INR|\$|USD|€|EUR)\s?[\d,]+(?:\.\d+)?", text, re.I)
    emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    parties = re.findall(r"(?:petitioner|respondent|plaintiff|defendant|employer|employee|landlord|tenant|party)\s*[:\-]\s*([^\n,;]{2,100})", text, re.I)
    return {
        "dates": list(dict.fromkeys(dates))[:20],
        "money": list(dict.fromkeys(money))[:20],
        "emails": list(dict.fromkeys(emails))[:20],
        "parties": [x.strip() for x in parties[:20]]
    }

def detect_clauses(text):
    low = text.lower()
    return [name for name, words in CLAUSES.items() if any(w in low for w in words)]

import re
from sklearn.feature_extraction.text import TfidfVectorizer

def split_sentences(text):
    text = re.sub(r"\s+", " ", text).strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text) if len(s.strip()) > 30]

def summarize(text, level="medium"):
    sentences = split_sentences(text)
    if not sentences:
        return "No meaningful text was extracted."
    if len(sentences) <= 5:
        return " ".join(sentences)

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=4000)
    matrix = vectorizer.fit_transform(sentences)
    scores = matrix.sum(axis=1).A1

    legal_terms = ["court", "agreement", "party", "parties", "shall", "hereby",
                   "claim", "order", "judgment", "liability", "termination",
                   "payment", "confidential", "dispute", "law", "obligation"]
    for i, sentence in enumerate(sentences):
        scores[i] += sum(0.12 for term in legal_terms if term in sentence.lower())

    count = {"short": 5, "medium": 9, "long": 15}.get(level, 9)
    count = min(count, len(sentences))
    indexes = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)[:count]
    indexes.sort()
    return " ".join(sentences[i] for i in indexes)

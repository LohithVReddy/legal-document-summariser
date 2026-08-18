import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def answer_question(question, pages):
    chunks = []
    for page in pages:
        for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", page["text"]):
            sentence = sentence.strip()
            if len(sentence) >= 30:
                chunks.append((page["page"], sentence))

    if not chunks:
        return {"answer": "No searchable text was found.", "sources": []}

    texts = [x[1] for x in chunks]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(texts + [question])
    similarities = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    best = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)[:3]
    selected = [chunks[i] for i in best if similarities[i] > 0]

    if not selected:
        return {"answer": "I could not find enough evidence in the document.", "sources": []}

    return {
        "answer": " ".join(x[1] for x in selected),
        "sources": [{"page": x[0], "text": x[1]} for x in selected]
    }

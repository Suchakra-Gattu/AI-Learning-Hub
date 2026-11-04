"""Stage 1: the smallest RAG that works.

Run:  python stage1_poc.py "How long do I have to return a tent?"

Three steps:
  1. Cut the documents into pieces (here: one piece per paragraph).
  2. Find the pieces that share the most words with the question.
  3. Paste those pieces into a prompt and ask the model.
"""
import sys
from common import load_documents, content_words, build_prompt, ask_llm


def split_into_paragraphs(docs):
    pieces = []
    for doc in docs:
        for para in doc["text"].split("\n\n"):
            if para.strip():
                pieces.append({"source": doc["source"], "text": para.strip()})
    return pieces


def retrieve(question, pieces, k=3):
    """Score = how many question words show up in the piece."""
    q_words = set(content_words(question))
    scored = []
    for p in pieces:
        overlap = len(q_words & set(content_words(p["text"])))
        scored.append((overlap, p))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [p for score, p in scored[:k] if score > 0]


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "How long do I have to return a tent?"
    pieces = split_into_paragraphs(load_documents())
    top = retrieve(question, pieces)
    print(f"Found {len(top)} pieces:")
    for p in top:
        print(f"  - {p['source']}: {p['text'][:70]}...")
    print()
    print(ask_llm(build_prompt(question, top)))

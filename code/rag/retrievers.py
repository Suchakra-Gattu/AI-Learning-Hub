"""Three ways to find chunks. Each one is a function: (question, chunks, k) -> top chunks.

  overlap_search : stage 1. Count shared words.
  bm25_search    : smarter word matching. Rare words count more. Long chunks do not win just for being long.
  vector_search  : turn text into a list of numbers and compare the lists. Here we use
                   character pieces (a toy). Real embeddings come from a model, see lesson 6.
  hybrid_search  : merge the rankings of bm25 and vector search.
"""
import math
from collections import Counter
from common import content_words, tokenize


def overlap_search(question, chunks, k=3):
    q = set(content_words(question))
    scored = sorted(((len(q & set(content_words(c["text"]))), i) for i, c in enumerate(chunks)), reverse=True)
    return [chunks[i] for s, i in scored[:k] if s > 0]


# ---------- BM25 ----------
def bm25_search(question, chunks, k=3, k1=1.5, b=0.75):
    docs = [content_words(c["text"]) for c in chunks]
    n = len(docs)
    avg_len = sum(len(d) for d in docs) / n
    df = Counter()
    for d in docs:
        df.update(set(d))
    q = content_words(question)
    scores = []
    for i, d in enumerate(docs):
        tf = Counter(d)
        s = 0.0
        for w in q:
            if w not in tf:
                continue
            idf = math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5))
            s += idf * tf[w] * (k1 + 1) / (tf[w] + k1 * (1 - b + b * len(d) / avg_len))
        scores.append((s, i))
    scores.sort(reverse=True)
    return [chunks[i] for s, i in scores[:k] if s > 0]


# ---------- Toy vector search ----------
def _grams(text, n=3):
    t = " ".join(tokenize(text))
    return Counter(t[i : i + n] for i in range(len(t) - n + 1))


def _cosine(a, b):
    dot = sum(a[g] * b[g] for g in a if g in b)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def vector_search(question, chunks, k=3):
    q = _grams(question)
    scored = sorted(((_cosine(q, _grams(c["text"])), i) for i, c in enumerate(chunks)), reverse=True)
    return [chunks[i] for s, i in scored[:k] if s > 0]


# ---------- Hybrid ----------
def hybrid_search(question, chunks, k=3, pool=8):
    """Reciprocal rank fusion: a chunk ranked high by either method rises to the top."""
    ranked_lists = [bm25_search(question, chunks, pool), vector_search(question, chunks, pool)]
    score = Counter()
    by_text = {}
    for ranking in ranked_lists:
        for rank, c in enumerate(ranking):
            score[c["text"]] += 1 / (60 + rank + 1)
            by_text[c["text"]] = c
    return [by_text[t] for t, s in score.most_common(k)]

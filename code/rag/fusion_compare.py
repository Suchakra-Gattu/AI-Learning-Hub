"""Two ways to mix keyword and vector search, and one way to search with several questions.

Run:  python fusion_compare.py

  rrf              : reciprocal rank fusion. Uses only positions in each list, not scores.
  weighted, raw    : w * vector score + (1 - w) * BM25 score, as they come out.
  weighted, scaled : the same, after squashing each list's scores to 0..1 (min-max).
  multi-query      : search several versions of the question, merge the lists with RRF.

All on the same chunks and the same 20 questions. No model needed.
"""
import json
from collections import Counter
from pathlib import Path
from common import load_documents, content_words
from chunking import chunk_all
from retrievers import bm25_scores, vector_scores, hybrid_search
from stage3_eval import evaluate
from stage5_advanced import SYNONYMS


def min_max(scores):
    """Squash a list of scores to 0..1. The best becomes 1, the worst 0."""
    lo, hi = min(scores), max(scores)
    return [(s - lo) / (hi - lo) if hi > lo else 0.0 for s in scores]


def weighted(w, scale):
    def search(question, chunks, k=3):
        kw, vec = bm25_scores(question, chunks), vector_scores(question, chunks)
        if scale:
            kw, vec = min_max(kw), min_max(vec)
        blended = [w * v + (1 - w) * t for t, v in zip(kw, vec)]
        order = sorted(range(len(chunks)), key=lambda i: blended[i], reverse=True)
        return [chunks[i] for i in order[:k]]
    return search


def rewrites(question):
    """shortcut: hand-written synonyms stand in for a model that writes 3 to 5 versions."""
    out = [question]
    for w in content_words(question):
        for key, syns in SYNONYMS.items():
            if w.startswith(key):
                out += [question.replace(w, s) for s in syns]
    return out


def multi_query(question, chunks, k=3):
    """Run hybrid search for each version, then fuse all the lists with RRF."""
    score, by_text = Counter(), {}
    for q in rewrites(question):
        for rank, c in enumerate(hybrid_search(q, chunks, k=8)):
            score[c["text"]] += 1 / (60 + rank + 1)
            by_text[c["text"]] = c
    return [by_text[t] for t, _ in score.most_common(k)]


if __name__ == "__main__":
    questions = json.loads((Path(__file__).parent / "eval_questions.json").read_text(encoding="utf-8"))
    chunks = chunk_all(load_documents())
    q = questions[0]["question"]
    kw, vec = bm25_scores(q, chunks), vector_scores(q, chunks)
    print(f'Score ranges for "{q}":')
    print(f"  bm25   {min(kw):.2f} .. {max(kw):.2f}")
    print(f"  vector {min(vec):.2f} .. {max(vec):.2f}")
    share = sum(0.7 * max(vector_scores(x["question"], chunks)) /
                (0.7 * max(vector_scores(x["question"], chunks)) + 0.3 * max(bm25_scores(x["question"], chunks)))
                for x in questions) / len(questions)
    print(f"  with w=0.7 on raw scores, vector's share of the top score is only {share:.0%} on average\n")

    print(f"{len(questions)} questions, top 3 chunks each\n")
    evaluate("rrf", hybrid_search, chunks, questions)
    for w in (0.3, 0.5, 0.7):
        evaluate(f"weighted raw w={w}", weighted(w, scale=False), chunks, questions)
    for w in (0.3, 0.5, 0.7):
        evaluate(f"weighted scaled w={w}", weighted(w, scale=True), chunks, questions)
    evaluate("multi-query + rrf", multi_query, chunks, questions)
    print(f'\nversions searched for "{questions[1]["question"]}":')
    for r in rewrites(questions[1]["question"]):
        print("  -", r)

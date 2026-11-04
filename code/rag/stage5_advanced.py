"""Stage 5: three upgrades, each measured on the same 20 questions. No model needed.

Run:  python stage5_advanced.py

  1. context label : does 'Title > Section' at the top of a chunk help search?
  2. rerank        : fetch 8 candidates, re-order them with a second, stricter score
  3. expand        : search with extra words for the same idea, merge the results

All three are toys that show the shape of the idea. In production the reranker is
a cross-encoder model and the expander is a model call. See the lessons.
"""
import json
from pathlib import Path
from common import load_documents, content_words
from chunking import chunk_all
from retrievers import bm25_search
from stage3_eval import evaluate

# shortcut: hand-written synonyms stand in for a model that rewrites the question. Use a model call for real data.
SYNONYMS = {"refund": ["money", "reimbursement"], "return": ["send", "back"], "ship": ["delivery", "deliver"],
            "broken": ["defect", "damaged"], "fix": ["repair"], "cost": ["fee", "price", "charge"]}


def strip_label(chunks):
    """Remove the 'Title > Section' first line, to see what the label was worth."""
    return [{**c, "text": c["text"].split("\n", 1)[1]} for c in chunks]


def rerank_search(question, chunks, k=3, pool=8):
    """Take 8 BM25 candidates, then score each by how many question words AND word pairs it contains."""
    q = content_words(question)
    pairs = set(zip(q, q[1:]))

    def score(chunk):
        words = content_words(chunk["text"])
        return len(set(q) & set(words)) + 2 * len(pairs & set(zip(words, words[1:])))

    return sorted(bm25_search(question, chunks, pool), key=score, reverse=True)[:k]


def expand_search(question, chunks, k=3):
    """Search the original question plus a copy with synonyms added. Merge, keep first-seen order."""
    extra = [s for w in content_words(question) for key, syns in SYNONYMS.items() if w.startswith(key) for s in syns]
    seen, merged = set(), []
    for q in (question, question + " " + " ".join(extra)):
        for c in bm25_search(q, chunks, k):
            if c["text"] not in seen:
                seen.add(c["text"])
                merged.append(c)
    return merged[:k]


if __name__ == "__main__":
    questions = json.loads((Path(__file__).parent / "eval_questions.json").read_text(encoding="utf-8"))
    chunks = chunk_all(load_documents())
    print(f"{len(questions)} questions, top 3 chunks each\n")
    evaluate("bm25, no label", bm25_search, strip_label(chunks), questions)
    evaluate("bm25 + context label", bm25_search, chunks, questions)
    evaluate("+ rerank (toy)", rerank_search, chunks, questions)
    evaluate("+ expansion (toy)", expand_search, chunks, questions)

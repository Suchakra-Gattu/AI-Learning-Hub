"""Stage 3: measure it. No model needed.

Run:  python stage3_eval.py

For each question we know which file and which fact the answer needs.
We check whether retrieval brought that fact into the top k chunks.
  top-1    : how often the right chunk is ranked first
  top-k    : how often the right chunk is anywhere in the top k
  MRR      : how HIGH in the list it is (1.0 = always first)
"""
import json
from pathlib import Path
from common import load_documents
from chunking import chunk_all
from retrievers import overlap_search, bm25_search, vector_search, hybrid_search
from stage1_poc import split_into_paragraphs, retrieve as stage1_retrieve


def evaluate(name, search, chunks, questions, k=3):
    hits, first, rr, misses = 0, 0, 0.0, []
    for q in questions:
        results = search(q["question"], chunks, k)
        rank = next((i + 1 for i, c in enumerate(results) if q["must_contain"].lower() in c["text"].lower()), None)
        if rank:
            hits += 1
            first += rank == 1
            rr += 1 / rank
        else:
            misses.append(q["question"])
    n = len(questions)
    print(f"{name:<22} top-1 {first / n:4.0%}   top-{k} {hits / n:4.0%}   MRR {rr / n:.2f}")
    return misses


if __name__ == "__main__":
    questions = json.loads((Path(__file__).parent / "eval_questions.json").read_text(encoding="utf-8"))
    docs = load_documents()
    paragraphs = split_into_paragraphs(docs)
    chunks = chunk_all(docs)

    print(f"{len(questions)} questions, top 3 chunks each\n")
    evaluate("stage 1 (overlap)", lambda q, c, k: stage1_retrieve(q, c, k), paragraphs, questions)
    evaluate("overlap + new chunks", overlap_search, chunks, questions)
    misses = evaluate("bm25", bm25_search, chunks, questions)
    evaluate("vector (toy)", vector_search, chunks, questions)
    evaluate("hybrid", hybrid_search, chunks, questions)
    if misses:
        print("\nQuestions bm25 missed:")
        for m in misses:
            print("  -", m)

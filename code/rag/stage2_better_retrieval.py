"""Stage 2: better chunks, better search, and sources in the answer.

Run:  python stage2_better_retrieval.py "Can I return a sleeping bag I slept in?"
Try:  python stage2_better_retrieval.py "how much for express delivery" --method vector
"""
import sys
from common import load_documents, build_prompt, ask_llm
from chunking import chunk_all
from retrievers import overlap_search, bm25_search, vector_search, hybrid_search

METHODS = {"overlap": overlap_search, "bm25": bm25_search, "vector": vector_search, "hybrid": hybrid_search}

if __name__ == "__main__":
    args = sys.argv[1:]
    method = "hybrid"
    if "--method" in args:
        i = args.index("--method")
        method = args[i + 1]
        args = args[:i] + args[i + 2 :]
    question = " ".join(args) or "Can I return a sleeping bag I slept in?"

    chunks = chunk_all(load_documents())
    top = METHODS[method](question, chunks, k=3)
    print(f"Method: {method}. Found {len(top)} chunks:")
    for c in top:
        print(f"  - {c['source']}: {c['text'].splitlines()[0]}")
    print()
    print(ask_llm(build_prompt(question, top)))

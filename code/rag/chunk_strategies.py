"""Five ways to cut the same documents, each measured on the same 20 questions. No model needed.

Run:  python chunk_strategies.py

  fixed words     : 40-word windows, no headings. The simplest cut.
  by headings     : what chunking.py does. One section per chunk, 'Title > Section' on top.
  semantic        : cut between sentences when the topic seems to change.
  sentence window : search single sentences, hand the model the sentence plus its neighbours.
  parent / child  : search single sentences, hand the model the whole section they came from.

Every strategy uses the same BM25 search, so only the cutting changes.
"""
import json
import re
from pathlib import Path
from common import load_documents
from chunking import chunk_all
from retrievers import bm25_search, _grams, _cosine
from stage3_eval import evaluate


def sections(doc):
    """Yield (label, sentences) for each '## ' section of a markdown document."""
    text = doc["text"]
    title = re.match(r"#\s+(.*)", text).group(1).strip()
    for block in re.split(r"\n(?=## )", text):
        lines = block.strip().splitlines()
        body = " ".join(l.strip() for l in lines[1:] if l.strip())
        if body:
            yield f"{title} > {lines[0].lstrip('# ').strip()}", re.split(r"(?<=[.!?])\s+", body)


def fixed_words(docs, size=40):
    out = []
    for d in docs:
        words = re.sub(r"#+ .*\n", " ", d["text"]).split()  # drop headings
        for i in range(0, len(words), size):
            out.append({"source": d["source"], "text": " ".join(words[i : i + size])})
    return out


def semantic(docs, threshold=0.25):
    """Join neighbouring sentences while they look alike. Cut where similarity drops.

    shortcut: _grams is a toy stand-in for a real embedding model. With real embeddings the
    threshold is usually picked from the spread of neighbour distances, not hard-coded.
    """
    out = []
    for d in docs:
        title = re.match(r"#\s+(.*)", d["text"]).group(1).strip()
        sentences = [s for _, sents in sections(d) for s in sents]  # ignore the headings on purpose
        current = [sentences[0]]
        for prev, nxt in zip(sentences, sentences[1:]):
            if _cosine(_grams(prev), _grams(nxt)) < threshold:
                out.append({"source": d["source"], "text": f"{title}\n{' '.join(current)}"})
                current = []
            current.append(nxt)
        out.append({"source": d["source"], "text": f"{title}\n{' '.join(current)}"})
    return out


def sentence_units(docs):
    """One unit per sentence. Each knows its neighbours and its whole section."""
    out = []
    for d in docs:
        for label, sents in sections(d):
            for i, s in enumerate(sents):
                out.append({
                    "source": d["source"],
                    "text": f"{label}\n{s}",  # what we search on
                    "window": f"{label}\n{' '.join(sents[max(0, i - 1) : i + 2])}",
                    "parent": f"{label}\n{' '.join(sents)}",
                })
    return out


def expand_to(field):
    """Search the small units, but return a bigger piece of text. Skip repeats."""
    def search(question, units, k=3):
        seen, out = set(), []
        for u in bm25_search(question, units, k * 4):
            if u[field] not in seen:
                seen.add(u[field])
                out.append({"source": u["source"], "text": u[field]})
            if len(out) == k:
                break
        return out
    return search


def words_sent(search, units, questions, k=3):
    """Average words the model would read per question. Bigger pieces cost more tokens."""
    total = sum(len(c["text"].split()) for q in questions for c in search(q["question"], units, k))
    return total / len(questions)


if __name__ == "__main__":
    questions = json.loads((Path(__file__).parent / "eval_questions.json").read_text(encoding="utf-8"))
    docs = load_documents()
    units = sentence_units(docs)
    runs = [
        ("fixed words", bm25_search, fixed_words(docs)),
        ("by headings", bm25_search, chunk_all(docs)),
        ("semantic", bm25_search, semantic(docs)),
        ("sentence window", expand_to("window"), units),
        ("parent / child", expand_to("parent"), units),
    ]
    print(f"{len(questions)} questions, top 3 pieces each\n")
    for name, search, pieces in runs:
        evaluate(name, search, pieces, questions)
    print("\npieces stored, and words sent to the model per question (top 3):")
    for name, search, pieces in runs:
        print(f"  {name:<18} {len(pieces):3} pieces  {words_sent(search, pieces, questions):4.0f} words")
    print("\nsemantic: the cut-off decides everything")
    for t in (0.10, 0.15, 0.20, 0.25):
        evaluate(f"  threshold {t:.2f} ({len(semantic(docs, t))} pc)", bm25_search, semantic(docs, t), questions)

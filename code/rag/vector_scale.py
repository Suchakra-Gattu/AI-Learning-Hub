"""Shrinking vectors: how much do you lose when you store them smaller? No model needed.

Run:  python vector_scale.py

We make toy dense vectors (256 numbers each) from character pieces, the same idea
as the toy vector search in retrievers.py. Then we store them four ways:

  float32 : 4 bytes per number. The full-size baseline.
  int8    : 1 byte per number. Each number rounded to one of 255 steps.
  binary  : 1 bit per number. Keep only the sign (+ or -).
  first 64: keep only the first 64 numbers. Real "Matryoshka" models are trained so this
            works; our toy vectors were not, so treat this row as the mechanics only.

For each, we check two things on the 20 questions:
  agree@3 : how many of the exact top 3 the smaller version also returns
  quality : the usual top-1 / top-3 / MRR from stage3_eval
"""
import json
import math
import random
import zlib
from pathlib import Path
from common import load_documents, tokenize
from chunk_strategies import sentence_units
from stage3_eval import evaluate

DIMS = 256


_PIECE_VECTORS = {}


def _piece_vector(piece, dims):
    """Each 3-letter piece gets its own fixed random direction (seeded, so runs repeat)."""
    if piece not in _PIECE_VECTORS:
        rng = random.Random(zlib.crc32(piece.encode()))
        _PIECE_VECTORS[piece] = [rng.gauss(0, 1) for _ in range(dims)]
    return _PIECE_VECTORS[piece]


def embed(text, dims=DIMS):
    """shortcut: a sum of random directions for each character 3-gram, not a real model.

    This makes every number in the vector non-zero, like a real embedding.
    """
    t = " ".join(tokenize(text))
    v = [0.0] * dims
    for i in range(len(t) - 2):
        for j, x in enumerate(_piece_vector(t[i : i + 3], dims)):
            v[j] += x
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def to_int8(v):
    """Round each number to a whole step between -127 and 127. Keep the step size to undo it."""
    step = (max(abs(x) for x in v) or 1.0) / 127
    return [round(x / step) for x in v], step


def to_bits(v):
    return [1 if x > 0 else 0 for x in v]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def hamming_score(a, b):
    """Bits that agree. Real systems do this with one CPU instruction per 64 bits."""
    return sum(x == y for x, y in zip(a, b))


STORES = {
    #  name        bytes per vector   encode the stored chunk       score(question vector, stored)
    "float32":  (DIMS * 4,          lambda v: v,                  dot),
    "int8":     (DIMS + 4,          to_int8,                      lambda q, s: dot(q, s[0]) * s[1]),
    "binary":   (DIMS // 8,         to_bits,                      lambda q, s: hamming_score(to_bits(q), s)),
    "first 64": (64 * 4,            lambda v: v[:64],             lambda q, s: dot(q[:64], s)),
}


def make_search(name, units):
    _, encode, score = STORES[name]
    stored = [encode(embed(u["text"])) for u in units]

    def search(question, _units, k=3):
        q = embed(question)
        ranked = sorted(range(len(units)), key=lambda i: score(q, stored[i]), reverse=True)
        return [units[i] for i in ranked[:k]]
    return search


if __name__ == "__main__":
    questions = json.loads((Path(__file__).parent / "eval_questions.json").read_text(encoding="utf-8"))
    units = sentence_units(load_documents())
    searches = {name: make_search(name, units) for name in STORES}
    exact = {q["question"]: {u["text"] for u in searches["float32"](q["question"], units)} for q in questions}

    print(f"{len(units)} sentences, {DIMS}-number vectors, {len(questions)} questions\n")
    print(f"{'store':<10} {'bytes':>6}  {'agree@3':>7}")
    for name, (size, _, _) in STORES.items():
        agree = sum(len(exact[q["question"]] & {u["text"] for u in searches[name](q["question"], units)})
                    for q in questions) / (3 * len(questions))
        print(f"{name:<10} {size:>6}  {agree:7.0%}")
    print()
    for name in STORES:
        evaluate(name, searches[name], units, questions)

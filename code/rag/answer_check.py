"""Check an answer against the chunks it was written from. No model needed.

Run:  python answer_check.py

For each sentence in the answer we ask: which retrieved chunk backs it up, and how well?
  support  : share of the sentence's meaning words found in its best chunk
  numbers  : every number in the sentence must appear in that chunk, or it fails
  citation : the best chunk's number, added after the fact if the model gave none

shortcut: word overlap stands in for a model judge. A real faithfulness check asks a model
"does this passage support this claim?", which catches paraphrases that word overlap misses.
"""
import re
from common import load_documents, content_words
from chunking import chunk_all
from retrievers import hybrid_search

SUPPORTED = 0.6

QUESTION = "How long do I have to return a tent?"
ANSWERS = {
    "grounded": "Tents can be returned within 60 days if they have not been slept in. "
                "Most other items must be returned within 30 days of delivery.",
    "invented": "Tents can be returned within 60 days if they have not been slept in. "
                "Used tents can still be returned for 50 percent store credit.",
}


def sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def check_sentence(sentence, chunks):
    words = set(content_words(sentence))
    numbers = set(re.findall(r"\d+", sentence))
    best, best_score = None, 0.0
    for i, c in enumerate(chunks):
        chunk_words = set(content_words(c["text"]))
        score = len(words & chunk_words) / len(words) if words else 0.0
        if numbers - set(re.findall(r"\d+", c["text"])):
            score = min(score, SUPPORTED - 0.01)  # a number the chunk never says is not supported
        if score > best_score:
            best, best_score = i, score
    return best, best_score


def check(answer, chunks):
    cited, rows = set(), []
    for s in sentences(answer):
        i, score = check_sentence(s, chunks)
        ok = score >= SUPPORTED
        if ok:
            cited.add(i)
        rows.append((ok, score, i, s))
    return rows, cited


if __name__ == "__main__":
    chunks = hybrid_search(QUESTION, chunk_all(load_documents()), k=3)
    print(f"Question: {QUESTION}\nRetrieved:")
    for i, c in enumerate(chunks):
        print(f"  [{i + 1}] {c['text'].splitlines()[0]}")
    for name, answer in ANSWERS.items():
        rows, cited = check(answer, chunks)
        faithful = sum(ok for ok, *_ in rows) / len(rows)
        print(f"\n{name}: faithfulness {faithful:.0%}, chunks actually used {len(cited)} of {len(chunks)}")
        for ok, score, i, s in rows:
            mark = f"[{i + 1}]" if ok else "UNSUPPORTED"
            print(f"  {score:4.0%}  {mark:<11} {s}")

"""The shape of every eval tool: dataset, target, evaluators, experiment. Standard library only.

Run: python mini_eval.py

LangSmith, Langfuse, Opik and RAGAS all do this loop at larger scale. Here it is in 40 lines.
"""
import json

# Dataset: inputs plus a reference answer. The app under test never sees the reference.
DATASET = [
    {"input": "Shut up, idiot", "reference": "toxic"},
    {"input": "Thanks, that was helpful", "reference": "ok"},
    {"input": "You are useless", "reference": "toxic"},
    {"input": "Where is my order?", "reference": "ok"},
]


# shortcut: a keyword rule stands in for a model call, so the eval runs offline. Swap in your real app here.
def target(text):
    return "toxic" if any(w in text.lower() for w in ("idiot", "shut up")) else "ok"


# Evaluators: score one (output, reference) pair. Return 1 or 0, or a number between.
def exact_match(output, reference):
    return int(output == reference)


def run_experiment(name, app, dataset, evaluators):
    rows = []
    for ex in dataset:
        out = app(ex["input"])
        rows.append({"input": ex["input"], "output": out, **{e.__name__: e(out, ex["reference"]) for e in evaluators}})
    scores = {e.__name__: sum(r[e.__name__] for r in rows) / len(rows) for e in evaluators}
    print(f"experiment {name}: {json.dumps(scores)}")
    for r in rows:
        if not all(r[e.__name__] for e in evaluators):
            print("  failed:", r)  # the failures are where you learn something
    return scores


if __name__ == "__main__":
    scores = run_experiment("baseline", target, DATASET, [exact_match])
    assert scores["exact_match"] == 0.75  # "You are useless" is missed, on purpose

---
title: Agentic RAG, letting the model decide how to search
summary: Normal RAG searches once. Agentic RAG lets the model search, look at the results, and try again. It helps on hard questions and costs more.
time: 15 min
---

Normal RAG is a straight line: question, search, answer. If the search misses, the answer is bad, and nothing tries again.

**Agentic RAG** puts search inside a loop the model controls:

1. Look at the question. Does it need a search at all?
2. Search.
3. Check the results. Are they good enough?
4. If not, rewrite the question and search again. If yes, answer.

```python
def agentic_answer(question, max_rounds=3):
    query = question
    for _ in range(max_rounds):                  # a hard limit, always
        chunks = search(query)
        verdict = grade(question, chunks)        # a model call: "good" or "bad"
        if verdict == "good":
            return answer(question, chunks)
        query = rewrite(question, chunks)        # a model call: try new words
    return "I could not find that in the documents."
```

This is a sketch, not tested code: `search`, `grade`, `rewrite` and `answer` are placeholders for the pieces you already built.

## Ideas from research

These are named in the Awesome-RAG list. We read their abstracts or pages only:

- **Corrective RAG (CRAG).** A small checker scores the retrieved text. If it is poor, the system searches elsewhere, such as the web, or drops the useless parts ([paper](https://arxiv.org/abs/2401.15884)).
- **Self-RAG.** A specially trained model decides when to look things up and checks its own claims against sources ([page](https://selfrag.github.io/)). It needs special training, so most teams copy the idea with a plain loop like the one above.

## What it costs

| Gain | Price |
|---|---|
| Handles questions that need two searches | 2 to 4 times the model calls |
| Recovers from a bad first search | Slower answers |
| Can pick between sources | Harder to test and debug |

:::warn Always cap the loop
Without `max_rounds`, a confused model can search forever and spend your budget. Set a hard limit, log each round, and fall back to "I could not find that".
:::

Use it when single-search recall is the problem you have measured. Otherwise, fix chunking and search first. This pattern is the bridge to the [Harness track](lesson:harness/the-agent-loop), where the same loop appears with tools and permissions.

:::check Why is a round limit non-negotiable in an agentic loop?
The loop is controlled by a model's judgment, which can fail. A fixed limit guarantees that cost and time stay bounded.
:::

Next: [beyond plain chunks](lesson:rag/beyond-chunks).

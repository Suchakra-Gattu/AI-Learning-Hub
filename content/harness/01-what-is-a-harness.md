---
title: What a harness is
summary: A model only produces text. Everything that lets it act safely in the real world is the harness.
time: 10 min
---

A language model does one thing: you give it text, it gives text back. It cannot open a file, run a command, or search your wiki. It cannot even remember what you said a minute ago unless you send that text again.

So how do coding assistants edit your files and run your tests? Something else does that work for the model. That something is the **harness**.

:::say
Agent = model + harness. The model decides what to try. The harness does it, safely, and keeps track.
:::

## The picture

```text
          you
           │ task
           ▼
   ┌───────────────────────────────────────────┐
   │                 HARNESS                   │
   │                                           │
   │   prompt builder ──► MODEL ──► "call tool X"
   │        ▲                          │       │
   │        │                          ▼       │
   │   session log ◄── results ◄── tool runner │
   │                         (permissions,     │
   │                          sandbox)         │
   └───────────────────────────────────────────┘
           │ files, shell, network, web
           ▼
        the real world
```

You will see the same boxes in every agent product, whatever name they use.

## The jobs of a harness

| Job | In plain words | Lesson |
|---|---|---|
| **The loop** | Ask the model, run what it asks for, show it the result, repeat until done | [2](lesson:harness/the-agent-loop) |
| **Tools** | The list of things the model may ask for, and the code that does them | [3](lesson:harness/tools-and-permissions) |
| **Permissions and sandbox** | Decide what runs freely, what needs a human yes, what is never allowed | [3](lesson:harness/tools-and-permissions) |
| **Context and memory** | Decide what text the model sees each turn, since it remembers nothing itself | [4](lesson:harness/context-memory-and-the-log) |
| **The log** | A permanent record of everything that happened | [4](lesson:harness/context-memory-and-the-log) |
| **Extensibility** | Let people add tools, models, and interfaces without rewriting the core | [5](lesson:harness/everything-is-a-plugin) |
| **Limits** | Step limits, time limits, cost limits, stop buttons | [2](lesson:harness/the-agent-loop) |

## How this connects to RAG

In the RAG track, your code decided every step: always search, then always answer. The model had no choice.

In an agent, the model chooses. "Search" is just one tool among many, and the model decides when to use it, with what words, and whether to search again. A RAG pipeline can sit inside an agent as a tool.

| | RAG pipeline | Agent with a harness |
|---|---|---|
| Who decides the steps | Your code | The model |
| Number of model calls | Usually one | Many, in a loop |
| Biggest risk | Wrong or made-up answer | Wrong **action** |
| What you must engineer | Search quality | Control, safety, and visibility |

That last row is why harness engineering is its own skill. When a bot can *do* things, mistakes cost more than a wrong sentence.

## Why learn this even if you never build one

- You will use harnesses daily (coding assistants, workflow tools). Knowing the parts tells you why they behave as they do.
- You will judge them. "Where does it log? What can it touch? How do I stop it?" are the questions that separate a safe tool from a risky one.
- You will extend them. Almost every serious harness has a plugin or tool system.

## What this track covers

1. What a harness is (this lesson).
2. [The agent loop](lesson:harness/the-agent-loop).
3. [Tools and permissions](lesson:harness/tools-and-permissions).
4. [Context, memory, and the session log](lesson:harness/context-memory-and-the-log).
5. [Everything is a plugin](lesson:harness/everything-is-a-plugin), the design idea behind DeepSeek Harness.
6. [A guided tour of DeepSeek Harness](lesson:harness/deepseek-harness-tour).
7. [Build a mini harness yourself](lesson:harness/build-a-mini-harness), about 120 lines that run.
8. [Safety and a harness checklist](lesson:harness/safety-and-checklist).

:::note About DeepSeek Harness
We use DeepSeek Harness as a worked example because its design is open and its documents explain it. This course does **not** build on top of it. The ideas apply to any harness. It is a developer preview that its authors say will change, so we link to its own docs for anything exact.
:::

:::check In one sentence, what is the difference between a model and an agent?
A model turns text into text. An agent is a model inside a harness, so it can take actions, see results, and keep going until the job is done.
:::

:::check Why is a wrong action usually worse than a wrong answer?
A wrong answer is text a person can read and reject. A wrong action, like deleting a file or sending an email, may already be done when anyone notices.
:::

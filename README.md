# AI Engineering, in plain words

A hands-on course for engineers and new graduates who want to build AI systems that work with real users. Every hard word is explained where it first appears, and there is a glossary.

It starts with how a model works, builds **RAG** (answering from your own documents) from a 50-line script to a production service, then covers agents, LangChain, testing, deployment, voice AI, fine-tuning, and model serving.

## Start learning

You need Node.js 18+ (for the site) and Python 3.9+ (for the code).

```bash
npm run dev
```

Open http://localhost:4173. Read a lesson, then run its code in a terminal beside it:

```bash
cd code/rag
python stage1_poc.py "How long do I have to return a tent?"
```

No `npm install` is needed. To build static files without the server: `npm run build`, then host the `dist/` folder anywhere.

## What is in the course

| Track | Lessons | What it covers |
|---|---|---|
| Foundations | 5 | Models, tokens, first API call, prompts, structured output |
| RAG: from POC to production | 18 | Chunking, search, rerank and rewrite, contextual chunks, agentic RAG, evals, safety, freshness, going live |
| Agents and LangChain | 4 | Agents, middleware, LangGraph, deep agents, managed deep agents, OpenWiki, integrations |
| Harness engineering | 8 | The loop, tools, permissions, logs, plugins, a tour of DeepSeek Harness, a mini harness |
| Evals and observability | 3 | Datasets, judges, live checks, LangSmith Engine, Insights |
| Voice AI | 4 | The STT, model, TTS chain, latency, turn-taking, WebRTC, SIP, LiveKit |
| LLMOps and fine-tuning | 5 | Prompt vs RAG vs fine-tune, training data, SFT, LoRA, DPO, MLflow, scoring, monitoring |
| Inference and edge | 4 | Prefill, decode, KV cache, vLLM, SGLang, TensorRT-LLM, Dynamo, GGUF, benchmarks |
| Deploy and monitor | 4 | Tracing, dashboards, alerts, hosting options, LLM gateway, the docs watcher |
| Dig deeper | 4 | Source notes for Awesome-RAG, ai-engineering-hub, LangChain, voice and LLMOps |

The RAG track and the Harness track are separate. The Harness track teaches the ideas with DeepSeek Harness as an example and does not build on top of it.

## The code

Code follows the [ponytail](https://github.com/DietrichGebert/ponytail) habit: the smallest thing that fully works. Where code skips something on purpose, a `shortcut:` comment says what and when to upgrade.

| Folder | What it is | Status |
|---|---|---|
| `code/foundations/` | First API call, token estimate, JSON checking | Run without an API key |
| `code/rag/` | Stages 1 to 5: POC, better search, eval, FastAPI service, advanced experiments | Run (service via FastAPI's test client) |
| `code/harness/mini_harness.py` | A tiny agent harness with a scripted model | Run |
| `code/agents/graph_demo.py` | LangGraph with a human pause, no model | Run with `langgraph` 1.2.19 |
| `code/evals/mini_eval.py` | Dataset, target, evaluator, experiment in 40 lines | Run |
| `code/voice/latency_timer.py` | Per-stage timing with simulated stages | Run |
| `code/llmops/` | Dataset split and LoRA parameter math | Run |
| `code/inference/kv_cache.py` | KV cache size formula | Run |
| `tools/docs_watcher.py` | Checks upstream LangChain pages our lessons cite and writes a diff report | Run, 37 pages |

**Not tested, and the lessons say so:** any live model API call, the `sentence-transformers` snippet in the RAG track, LangChain and LangSmith examples (they need keys and accounts), LiveKit, SIP, vLLM, SGLang, TensorRT-LLM, Dynamo, llama.cpp, MLflow, and DeepSeek Harness itself. Those lessons are explained from official docs with links.

RAG numbers come from `stage3_eval.py` and `stage5_advanced.py` on four short files and 20 questions. A one-question change is noise.

## The docs watcher

Lessons about fast-moving tools go stale. `python tools/docs_watcher.py` re-fetches the LangChain pages our lessons cite and writes a diff report to `watcher/reports/`. It never edits lessons. A person reads the report, then asks Claude to propose edits, and reviews them like any pull request. See the [lesson](content/deploy/04-watching-the-docs.md) for why.

## Repo layout

```
content/            lessons in Markdown, plus course.json and glossary.md
code/               runnable code for the lessons
tools/              docs_watcher.py
watcher/            snapshot of cited pages and change reports
research/           raw research notes (copies live in content/research/)
ui/                 site template, CSS, JS
scripts/            build.mjs (builder), dev.mjs (local server)
PRODUCT.md          who this is for
CONTRIBUTING.md     how to add or change lessons
```

## Adding lessons

See [CONTRIBUTING.md](CONTRIBUTING.md). Add a Markdown file to `content/<track>/`, name it with a number prefix, and run `npm run check`.

## About DeepSeek Harness

DeepSeek Harness is an open-source developer preview. Its authors warn of breaking changes and say it has not been security audited. The lessons use only what its documentation states and link to the official repo: https://github.com/deepseek-ai/deepseek-harness. If this course and the official docs disagree, trust the docs.

---
title: LangChain ecosystem, source notes
summary: Page-by-page notes on LangChain, LangGraph, Deep Agents, LangSmith, OpenWiki and the gateway, with what we could not verify.
time: 45 min
---


Researched 2026-11-03 from the official docs at docs.langchain.com. Every fact below comes from a page I fetched in this session. Nothing is filled from memory. Items I could not confirm are labeled UNVERIFIED.

Important caveat on code. The fetch tool summarizes pages with a small model. It sometimes shortens or rewrites code. Where the tool said it rewrote or trimmed code, I say so. Before putting any snippet in a lesson, copy it from the live page and run it.

Version note. The pages show model names such as `openai:gpt-5.5` and `claude-sonnet-5`. Those names change often. Do not pin lesson code to them without checking.

## 0. Map of the ecosystem

Start page: https://docs.langchain.com/build-overview

It lists these starting points:

| Product | One-line meaning (from the page) | URL |
|---|---|---|
| Managed Deep Agents | Deep agents on managed infrastructure. LangSmith runs the harness and runtime. | https://docs.langchain.com/langsmith/python/managed-deep-agents-overview.md |
| Deep Agents | The same harness, self-hosted or on a custom LangSmith Deployment. | https://docs.langchain.com/oss/python/deepagents/overview.md |
| LangChain | A minimal, configurable agent framework: models, tools, prompts, middleware. | https://docs.langchain.com/oss/python/langchain/overview.md |
| LangGraph | Low-level orchestration for stateful, long-running agents. | https://docs.langchain.com/oss/python/langgraph/overview.md |
| Fleet | No-code agent builder in LangSmith. | https://docs.langchain.com/langsmith/fleet.md |
| Deep Agents Code | Open source terminal coding agent (`dcode`). | https://docs.langchain.com/oss/deepagents/code/overview.md |
| OpenWiki | Wiki generator for codebases (section 5). | https://docs.langchain.com/oss/openwiki/overview.md |

Also on the page: Integrations, Learn, Reference, Contribute, and "Connect these docs via MCP" (https://docs.langchain.com/use-these-docs.md).

How the layers stack, as documented:
- LangChain agents are built on top of LangGraph (LangChain overview).
- Deep Agents adds planning, a virtual filesystem, and subagents on top of LangChain and LangGraph (Deep Agents overview).
- Managed Deep Agents runs Deep Agents on LangSmith Agent Server (Managed overview).
- LangSmith is the platform for tracing, evals, deployment, and monitoring.

Each Python page has a TypeScript twin under `/oss/javascript/...`. I read only the Python pages.

## 1. LangChain

### 1.1 Overview and agents

(a) Plain English. LangChain is a framework for building agents. An agent is a model that calls tools in a loop until the task is done. The docs say "Agent = Model + Harness". The harness is the prompt, the tools, and any middleware. The main entry point is `create_agent`. Under the hood it is a LangGraph graph, so it gets saving, pausing, and resuming from LangGraph.

(b) URLs read:
- https://docs.langchain.com/oss/python/langchain/overview.md
- https://docs.langchain.com/oss/python/langchain/agents.md

(c) Example, from the overview page. Version: the page gives no LangChain package version. Install line was shown for the OpenAI variant.

```bash
pip install -qU langchain "langchain[openai]"
```

```python
from langchain.agents import create_agent

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="openai:gpt-5.5",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]}
)
print(result["messages"][-1].content_blocks)
```

Source: https://docs.langchain.com/oss/python/langchain/overview.md

(d) Check before production:
- The page states no Python version and no package version. Pin both yourself.
- The agents page names `ModelRetryMiddleware(max_retries=3)` and `ToolRetryMiddleware(max_retries=2)` for rate limits and timeouts. It does not explain how to set a recursion or call cap there. Look at the model call limit middleware before shipping.
- Multi-turn memory needs a checkpointer and a `thread_id`. `InMemorySaver()` is for local use.

### 1.2 Models

(a) A model is the reasoning engine. You can call it directly or let an agent call it. `init_chat_model` builds a chat model from a name. Every provider uses the same interface, so you can switch providers with small changes. `max_retries` defaults to 6 (per the page).

(b) URL: https://docs.langchain.com/oss/python/langchain/models.md

(c) Example (Anthropic tab, as returned by the fetch tool):

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("claude-sonnet-4-6")
response = model.invoke("Why do parrots talk?")
```

Provider packages install like `pip install -U "langchain[openai]"`.

(d) Check: model names are passed straight to the provider API, so a retired name fails at run time. Set `timeout` and `max_tokens`.

### 1.3 Tools

(a) A tool is a function the model may ask your code to run. The docstring becomes the description the model reads. Type hints define the inputs. Tools can read run data through a `ToolRuntime` argument (state, context, store, stream writer).

(b) URL: https://docs.langchain.com/oss/python/langchain/tools.md

(c) Example:

```python
from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"It is currently sunny in {city}."
```

(d) Check:
- The names `config` and `runtime` are reserved argument names.
- Tool errors are meant to be handled by middleware (`@wrap_tool_call`), not by try/except in every tool.
- If a tool returns a `Command` that updates state, it must include a matching `ToolMessage`, or `ToolNode` raises `ValueError`.

### 1.4 Messages

(a) Messages are the units of context. There are four types: system, human (user), AI (assistant), tool. A tool message must reference the tool call ID it answers. Message `content` can be a string or a list of typed "content blocks" (text, reasoning, image, tool_call, and others) that look the same across providers.

(b) URL: https://docs.langchain.com/oss/python/langchain/messages.md

(c) Example:

```python
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, AIMessage, SystemMessage

model = init_chat_model("gpt-5-nano")

system_msg = SystemMessage("You are a helpful assistant.")
human_msg = HumanMessage("Hello, how are you?")

messages = [system_msg, human_msg]
response = model.invoke(messages)  # Returns AIMessage
```

(d) Check: `content_blocks` reads content in a standard shape. It does not replace `content`. To store standard blocks in `content`, set `output_version="v1"` or the `LC_OUTPUT_VERSION` variable.

### 1.5 Middleware

(a) Middleware is code that runs before and after each step of the agent loop. Uses: summarizing long chats, human approval, retries, model fallback, call limits, PII detection. Hooks run inside the compiled LangGraph.

(b) URLs:
- https://docs.langchain.com/oss/python/langchain/middleware/overview.md
- Also listed, not read: built-in (`/middleware/built-in.md`), custom (`/middleware/custom.md`).

(c) Example (the `...` are the page's own placeholders):

```python
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, HumanInTheLoopMiddleware

agent = create_agent(
    model="gpt-5.5",
    tools=[...],
    middleware=[
        SummarizationMiddleware(...),
        HumanInTheLoopMiddleware(...)
    ],
)
```

(d) Check: the overview page does not list hook names or the full set of built-ins. Read the built-in and custom pages first. Order of middleware may matter. UNVERIFIED, I did not read the order rules.

### 1.6 Structured output

(a) You can make an agent return data in a fixed shape (for example a Pydantic class) in `result["structured_response"]`. LangChain picks the provider's native method if there is one, else uses tool calling.

(b) URL: https://docs.langchain.com/oss/python/langchain/structured-output.md

(c) Example (a fragment; `ContactInfo` is defined elsewhere on the page):

```python
agent = create_agent(
    model="gpt-5.5",
    response_format=ContactInfo  # Auto-selects ProviderStrategy
)
```

(d) Check: with `ToolStrategy`, `handle_errors=True` (default) retries on validation errors by sending the error back to the model. Retries apply to `create_agent` only, not to plain `prompt | model | parser` chains.

### 1.7 RAG (retrieval augmented generation)

(a) RAG means: find relevant text first, then give it to the model with the question. The building blocks are: loader (file to `Document`), splitter (cut into chunks), embeddings (text to numbers), vector store (search by meaning), retriever (a standard search interface).

(b) URLs:
- https://docs.langchain.com/oss/python/langchain/knowledge-base.md
- https://docs.langchain.com/oss/python/deepagents/rag.md (RAG with Deep Agents)
- https://docs.langchain.com/oss/python/deepagents/retrieval.md (listed, not read)

(c) Examples from the knowledge-base page (fragments, not a full program):

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200, add_start_index=True
)
```

```python
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
```

```python
from langchain_core.vectorstores import InMemoryVectorStore
vector_store = InMemoryVectorStore(embeddings)
ids = vector_store.add_documents(documents=all_splits)
```

```python
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 1},
)
retriever.batch(["When was Nike incorporated?"])
```

No versions are pinned on that page.

(d) Check:
- `InMemoryVectorStore` loses data on restart. The Deep Agents RAG page says to persist the index and refresh it on a schedule in production.
- The Deep Agents RAG page says no prompt strategy fully stops indirect prompt injection, and tells you to check citations before showing answers.
- That page mixes model IDs and embedding models between its step-by-step and full script. Confirm what you use.
- `RubricMiddleware` (grader for answer grounding) is marked beta and needs `deepagents>=0.6.5`.
- Score from `similarity_search_with_score` is a distance, so lower is closer (per the page).

## 2. LangGraph

(a) Plain English. LangGraph lets you draw your program as a graph. State is shared data. Nodes are functions that read state and return changes. Edges say which node runs next. A "reducer" says how an update merges into state (replace, or append to a list). You must `compile` the graph before use. Compiling is where you attach a checkpointer.

(b) URLs read:
- https://docs.langchain.com/oss/python/langgraph/overview.md
- https://docs.langchain.com/oss/python/langgraph/graph-api.md
- https://docs.langchain.com/oss/python/langgraph/persistence.md
- https://docs.langchain.com/oss/python/langgraph/interrupts.md
- https://docs.langchain.com/oss/python/langgraph/streaming.md
- https://docs.langchain.com/oss/python/langgraph/durable-execution (see UNVERIFIED note below)

(c) Examples.

Install and minimal graph (overview page):

```bash
pip install -U langgraph
```

```python
from langgraph.graph import StateGraph, MessagesState, START, END

def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}

graph = StateGraph(MessagesState)
graph.add_node(mock_llm)
graph.add_edge(START, "mock_llm")
graph.add_edge("mock_llm", END)
graph = graph.compile()

graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
```

State with a reducer (graph-api page):

```python
from operator import add
from typing import Annotated
from typing_extensions import TypedDict

class State(TypedDict):
    foo: int
    bar: Annotated[list[str], add]
```

Persistence (persistence page):

```python
graph = builder.compile(checkpointer=checkpointer, store=store)

result = graph.invoke(
    {"messages": [{"role": "user", "content": "Hi, my name is Bob."}]},
    {"configurable": {"thread_id": "thread-1"}},
)
```

Pause for a human (interrupts page; only fragments shown there):

```python
approved = interrupt("Do you approve this action?")
```

```python
graph.stream_events(Command(resume=True), config=config, version="v3").output
```

Streaming (streaming page):

```python
for chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode="updates",
    version="v2",
):
    if chunk["type"] == "updates":
        print(chunk["data"])
```

Concept summary:
- Persistence: a thread is a conversation ID (`thread_id`). A checkpoint is a saved snapshot of the thread's state. A checkpointer saves and loads snapshots. A store keeps data that spans threads, such as user preferences.
- Human-in-the-loop: `interrupt()` pauses and saves state. You resume with `Command(resume=...)` on the same `thread_id`.
- Streaming modes: `values`, `updates`, `messages`, `custom`, `checkpoints`, `tasks`, `debug`. The page says "event streaming" is recommended for new apps (https://docs.langchain.com/oss/python/langgraph/event-streaming.md, listed, not read).
- Durable execution: see below.

Durable execution. Two fetches of `.../langgraph/durable-execution` and `.../durable-execution.md` returned the Persistence page, not a separate page. A web search result snippet says the canonical page covers: a checkpointer plus thread ID, wrapping non-deterministic or side-effect code in tasks, resume restarting at the beginning of the node, durability modes "exit", "async", "sync", and graceful shutdown needing `langgraph>=1.2`. I did not read that page directly. Treat these as UNVERIFIED until you read https://docs.langchain.com/oss/python/langgraph/durable-execution in a browser.

(d) Check before production:
- Do not use `InMemorySaver` in production. It loses data on restart. The page recommends `PostgresSaver` (async: `AsyncPostgresSaver`), and `SqliteSaver` for local work. Call `setup()` on first use of `PostgresSaver`.
- Keep `thread_id` under 255 characters for Postgres.
- Old checkpoints pile up. Plan a cleanup job.
- On resume, the paused node restarts from its top. Code before `interrupt()` runs again, so keep it safe to repeat.
- Do not wrap `interrupt()` in a broad try/except. Keep interrupt order stable.
- The typed resume value option (`response_schema`) needs `langgraph>=1.2.12`.
- Static breakpoints are for debugging only.

## 3. Deep Agents

(a) Plain English. Deep Agents is an "agent harness for complex, multi-step work". It wraps LangChain and LangGraph and adds:
- Planning: opt-in. Add `TodoListMiddleware` to get a `write_todos` tool that tracks tasks as pending, in progress, or completed. From v0.7 this is off by default.
- File system: a virtual filesystem with tools `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`. A "backend" decides where files really live. `execute` (shell) exists only with sandbox backends.
- Subagents: a built-in `task` tool hands a job to a helper agent. The helper works in its own context and returns one final report, which keeps the main agent's context small. A `general-purpose` subagent is on by default.
- Also: skills (loaded from `SKILL.md` files), memory (`AGENTS.md` files), history summarizing, and `interrupt_on` for approval.

(b) URLs read:
- https://docs.langchain.com/oss/python/deepagents/overview.md
- https://docs.langchain.com/oss/python/deepagents/subagents.md (first 100,000 of 105,087 characters)
- https://docs.langchain.com/oss/python/deepagents/backends.md
- https://docs.langchain.com/oss/python/deepagents/human-in-the-loop.md
- Listed, not read: dynamic subagents, async subagents.

(c) Examples.

The overview page's minimal example was described but not reproduced by the fetch tool. It uses `create_deep_agent` from `deepagents`, a `get_weather` function tool, a model string like `provider:model`, a `tools` list, and `system_prompt`, then `invoke`. Copy the exact text from the page. The overview page gave no install command (it links to PyPI package `deepagents`). UNVERIFIED install command.

Subagent (trimmed by the fetch tool):

```python
research_subagent = {
    "name": "research-agent",
    "description": "Used to research more in depth questions",
    "system_prompt": "You are a great researcher",
    "tools": [internet_search],
    "model": "openai:gpt-5.5",  # Optional override, defaults to main agent model
}
subagents = [research_subagent]

agent = create_deep_agent(
    model="google_genai:gemini-3.6-flash",
    subagents=subagents,
)
```

Backends (backends page):

```python
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, FilesystemBackend

agent = create_deep_agent(
    model="anthropic:claude-sonnet-5",
    backend=CompositeBackend(
        default=StateBackend(),  # Scratch space, thread-scoped
        routes={
            "/workspace/": FilesystemBackend(root_dir="/path/to/project", virtual_mode=True),
        },
    ),
)
```

Approval (human-in-the-loop page):

```python
interrupt_on={
    "remove_file": True,  # Default: approve, edit, reject, respond
    "fetch_file": False,  # No interrupts needed
    "notify_email": {"allowed_decisions": ["approve", "reject"]},  # No editing
}
```

Versions seen on these pages: `delete` tool and the `tools` allowlist on `FilesystemMiddleware` need `deepagents>=0.7`. Forked subagents (beta) need `deepagents>=0.7.13`. Structured output from subagents needs `deepagents>=0.5.3`.

(d) Check before production:
- `FilesystemBackend` and `LocalShellBackend` are for local tools and controlled CI. Do not use them in a web server. Use `StateBackend`, `StoreBackend`, or a sandbox.
- `FilesystemBackend` has no path limit unless `virtual_mode=True`.
- `LocalShellBackend` runs any command with your permissions.
- Agents can read `.env` files in reachable paths. Keep secrets out.
- `StoreBackend` without a namespace is shared by all users of one assistant. Set a per-user namespace.
- Human approval needs a checkpointer and the same `thread_id` on resume.
- Subagent pitfalls from the page: vague descriptions mean the main agent does the work itself. Setting `tools` replaces inherited tools. Skills are not inherited by custom subagents.
- Dynamic subagents are beta and need `langchain-quickjs` (Python 3.11+).

## 4. Managed Deep Agents

(a) Plain English. A LangSmith service. You write a project folder (instructions, tools, skills, model). The `mda` command uploads it and LangSmith runs it. LangSmith manages the Deep Agents harness, the runtime (LangSmith Agent Server: API, threads, runs, streaming, MCP endpoint), and platform features: sandboxes, durable memory, channels such as Slack, cron schedules, and OAuth connections. By contrast, `create_deep_agent` gives you an agent you host yourself.

Status: the quickstart and runtime pages say "public beta" on LangSmith Cloud. The overview page itself shows no beta label. The overview page does not document quotas or limits.

(b) URLs read:
- https://docs.langchain.com/langsmith/python/managed-deep-agents-overview.md
- https://docs.langchain.com/langsmith/python/managed-deep-agents-quickstart.md
- https://docs.langchain.com/langsmith/python/managed-deep-agents-runtime.md
- https://docs.langchain.com/langsmith/python/managed-deep-agents-evals.md
- Full list of about 33 pages is in https://docs.langchain.com/_llms/agent-development-lifecycle/build/python.txt (schedules, memory, sandboxes, deploy, CLI reference, and more).

(c) Examples (quickstart, as returned by the fetch tool):

```bash
uvx --from managed-deepagents mda init research-assistant
uv sync
uv run mda dev
uv run mda deploy
```

The overview page says the agent file starts with `from managed_deepagents import define_deep_agent` and the sample sets `model="openai:gpt-5.5"`. `define_deep_agent` returns a definition. The runtime compiles it with `create_deep_agent`.

Evals for managed agents use Harbor tasks:

```bash
uv run mda evals init -i
harbor run --config evals/harbor-job.json --yes
```

Source: managed-deep-agents-evals.md. The page also names `harbor[langsmith]==0.21.0` for viewing results.

(d) Check:
- Public beta, LangSmith Cloud only. Expect changes. The runtime page says `runtime.channel` is deprecated and goes away in `managed-deepagents` 0.11.
- Quickstart prerequisites: Python, `uv`, a model key, a LangSmith key.
- Plan, price, and usage limits: not on the pages I read. UNVERIFIED.
- Keep `.env` out of version control.
- Built-in Slack channel sends text only (runtime page).

## 5. OpenWiki

(a) Plain English. OpenWiki is documented in LangChain's own docs at docs.langchain.com/oss/openwiki. It is an open source command-line tool. It writes and keeps up to date a Markdown wiki about a codebase (or a personal knowledge base). The wiki is mainly for coding agents, which read it first and open source files only when needed. Humans can browse it in a local visualizer. The page says it is built on Deep Agents with LangSmith tracing. It ties key facts to versioned source evidence and refreshes pages when the evidence changes. Output follows "Open Knowledge Format (OKF v0.2)".

Modes: code mode (default) writes to an `openwiki/` folder in the repo and links it from `AGENTS.md` (and `CLAUDE.md` if present). Personal mode builds `~/.openwiki/wiki` from sources such as git repos, Gmail, Notion, and web search.

The pages do not name an author or a version number. The repo `langchain-ai/docs` contains an `openwiki/` directory (seen in the file listing) and a `docs-release-watch` agent that watches OpenWiki releases (section 14). That supports "LangChain project" but the docs page does not say it in words.

(b) URLs read:
- https://docs.langchain.com/oss/openwiki/overview.md
- https://docs.langchain.com/oss/openwiki/quickstart.md
- https://docs.langchain.com/oss/openwiki/automate-updates.md
- Listed, not read: integrations, search-and-link, visualize, cli-reference, customize, providers, code-mode, personal-mode (all under `/oss/openwiki/`).

(c) Examples (overview and quickstart):

```bash
npm install -g openwiki
openwiki --init
openwiki visualize
openwiki --update
```

Requires Node.js 22.22.0 or newer (quickstart). First run asks for a model provider, an API key, and an optional LangSmith key. Settings save to `~/.openwiki/.env`.

CI command (automate-updates page):

```bash
openwiki code --update --print
```

(d) Check:
- It calls a model provider and sends your code to it. Check your data rules first.
- Review the pull request it opens. It can change wiki Markdown, `openwiki/.claims/`, `AGENTS.md`, `CLAUDE.md`, and the workflow file.
- CI runs send anonymous telemetry. Set `OPENWIKI_TELEMETRY_DISABLED=1` to turn it off.
- Ephemeral CI runners restart from scratch after a failure unless the workspace is kept.
- No version number on the docs pages.

## 6. Integrations

(a) Plain English. The catalog lists tools you plug into LangChain. Two views: by provider (a company such as OpenAI) and by component type (chat models, embeddings, vector stores, document loaders, tools, middleware, checkpointers, sandboxes). Most provider packages are named `langchain-<provider>`. A few break the pattern (`databricks-langchain`, `toolbox-langchain`).

How to find one:
1. Open the providers overview, or the "all providers" page, or search by name.
2. Provider pages follow `.../integrations/providers/<name>.md`.
3. For vector stores, open the index. It has a "Top integrations" list with install and sample code, and a table with columns: Delete by ID, Filtering, Search by Vector, Search with score, Async, Passes Standard Tests, Multi Tenancy, IDs in add Documents, Downloads. A blank cell means unmarked, not "no".
4. For document loaders, open the index. Loaders are grouped by use (productivity, webpages, PDFs, cloud, file types). Every loader implements `BaseLoader` with `load()` and `lazy_load()`.

(b) URLs read:
- https://docs.langchain.com/oss/python/integrations/providers/overview.md
- https://docs.langchain.com/oss/python/integrations/vectorstores/index.md
- https://docs.langchain.com/oss/python/integrations/document_loaders/index.md
- Example entries: vectorstores/qdrant, vectorstores/pinecone, vectorstores/milvus, vectorstores/weaviate, document_loaders/unstructured_file, document_loaders/docling.

(c) Example: none specific. The RAG snippets in section 1.7 use `langchain-openai` (embeddings) and `langchain-core` (in-memory store). Other store packages named on the RAG page: `langchain-chroma`, `langchain-milvus`, `langchain-postgres`.

(d) Check:
- The loader page warns "Community document loaders are user-contributed and unverified."
- Metadata filter syntax differs between vector stores. Read the store's own page.
- Downloads are a popularity hint, not a fit test.
- `InMemoryVectorStore` is marked as not supporting "Search by Vector".

## 7. Testing and evaluation (LangSmith)

(a) Plain English.
- Dataset: a set of test cases. Each example has an input and an optional reference output (the good answer). The app never sees the reference output. Evaluators do.
- Experiment: the result of running one version of your app on a dataset. It stores outputs, scores, and traces.
- Evaluator: a scoring function. Kinds named in the docs: human review, code checks, LLM-as-judge, decision models, pairwise comparison.
- Offline evaluation: runs before deploy on a dataset. Good for benchmarks, regression tests, unit tests, backtests.
- Online evaluation: runs after deploy on real production runs and threads. There are no reference outputs, so it checks quality patterns, safety, anomalies.
- Refining prompts: LangSmith has a Playground and Prompt Hub. You edit a prompt, test it, and save a commit. Prompt Canvas and Playground Chat help improve prompts. Commits can be tagged. You can pin a prompt version as `"<prompt-name>:<commit-hash>"`.

(b) URLs read:
- https://docs.langchain.com/langsmith/evaluation.md
- https://docs.langchain.com/langsmith/evaluation-concepts.md
- https://docs.langchain.com/langsmith/evaluate-llm-application.md
- https://docs.langchain.com/langsmith/online-evaluations-llm-as-judge.md
- https://docs.langchain.com/langsmith/prompt-engineering-quickstart.md
- Listed, not read (from the index): evaluation-quickstart, manage-datasets, analyze-an-experiment, compare-experiment-results, annotation-queues, trajectory-evals, pytest, vitest-jest, openevals, evaluate-rag-tutorial, run-evaluation-from-playground, online-evaluations-code, online-evaluations-multi-turn, tuned-evaluators.

(c) Offline example. The fetch tool said it condensed and rewrote this. Version: needs `langsmith>=0.3.13` and `openai`. Source: https://docs.langchain.com/langsmith/evaluate-llm-application.md

```python
from langsmith import Client, evaluate
from openai import OpenAI

client = Client()
oai = OpenAI()

dataset = client.create_dataset("Toxic Queries")
client.create_examples(
    dataset_id=dataset.id,
    examples=[{"inputs": {"text": "Shut up, idiot"}, "outputs": {"label": "Toxic"}}],
)

def classify(inputs: dict) -> dict:
    resp = oai.chat.completions.create(
        model="gpt-5.4-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": "Reply 'Toxic' or 'Not toxic'."},
            {"role": "user", "content": inputs["text"]},
        ],
    )
    return {"class": resp.choices[0].message.content}

def correct(outputs: dict, reference_outputs: dict) -> bool:
    return outputs["class"] == reference_outputs["label"]

results = evaluate(
    classify,
    data="Toxic Queries",
    evaluators=[correct],
    experiment_prefix="baseline",
)
```

Prompt SDK example (prompt-engineering-quickstart.md; trimmed by the tool):

```python
prompt = ChatPromptTemplate([
    ("system", "You are a helpful chatbot."),
    ("user", "{question}"),
])

client.push_prompt("prompt-quickstart", object=prompt)
```

Online evaluator setup (UI, no code): open the tracing project, Evaluators tab, "+ Evaluator". Set filters, a sampling rate (0.1 means 10% of matching runs), and optional backfill of past runs.

(d) Check:
- Online evaluators cost model calls. Use sampling. There is a weekly spend limit per evaluator. When it is hit, the evaluator pauses until Monday 12AM UTC or an admin raises the limit.
- Any evaluator run auto-upgrades that trace to extended data retention (online evaluator page). That can raise cost.
- Backfill can only be set when you create the rule.
- A judge model is a model. Audit its scores. The index lists pages on this (`audit-evaluator-scores`, `improve-judge-evaluator-feedback`), not read.
- The sample uses model names such as `gpt-5.4-mini`. Check they exist for you.
- The evaluation overview page itself has no prompt-playground links. I found the prompt pages by search.

## 8. Deployment (LangSmith Deployment and Agent Server)

(a) Plain English. Agent Server is the runtime that serves a deployed agent. Its three ideas: assistants (configuration), threads (state), runs (work). It also supports cron jobs, streaming, human pauses, MCP and A2A endpoints, auth, custom routes, custom stores and checkpointers, encryption.

Options as documented:
- Cloud: LangChain runs everything (control plane, data plane, Agent Server, databases) on AWS and GCP. Needs a Plus plan or above. Two types: Serverless (scales to zero) and Dedicated (always on, autoscaling). Steps: check it runs with `langgraph dev`, then push to a connected GitHub repo or run `langgraph deploy`.
- Full self-hosted: you run Agent Server, control plane, data plane, and databases. LangChain gives images, Helm charts, and a license. The page says "Self-hosted deployments require an Enterprise plan."
- Hybrid: LangChain hosts the control plane. Agent Servers and databases run in your network.
- Standalone server: no control plane and no managed UI. You run the Agent Server API and workers with your own PostgreSQL and Redis. You can still send traces to LangSmith.

(b) URLs read:
- https://docs.langchain.com/langsmith/deploy-to-cloud-overview.md
- https://docs.langchain.com/langsmith/deploy-to-self-hosted-overview.md
- https://docs.langchain.com/langsmith/agent-server-overview.md
- https://docs.langchain.com/langsmith/deploy-standalone-server.md
- Index of 253 deploy pages: https://docs.langchain.com/_llms/agent-development-lifecycle/deploy.txt
- Listed, not read: application-structure, hybrid, deploy-with-control-plane, agent-server-scale, configure-checkpointer, env-var-cloud, env-var-self-hosted.

(c) Examples. Only commands shown on the pages:

```bash
langgraph dev
langgraph deploy
langgraph build
```

The standalone page says to check `/ok`, which should return `{"ok": true}`. It also names these variables: `DATABASE_URI`, `REDIS_URI`, `LANGSMITH_API_KEY`, `LANGGRAPH_CLOUD_LICENSE_KEY`. I did not find the CLI install command or a `langgraph.json` sample. The agent-server page links to https://docs.langchain.com/langsmith/application-structure.md for that. UNVERIFIED.

(d) Check:
- Standalone: the page warns "Do not run standalone servers in serverless environments." Kubernetes with the LangSmith Helm chart is the only path LangChain tests regularly. Other setups need you to build queue autoscaling, graceful draining, and upgrades.
- Standalone needs outbound access to `beacon.langchain.com` for license checks, unless air-gapped.
- Postgres holds assistants, threads, runs, memory, and the task queue. Plan backups.
- Hybrid and standalone plan or license needs are not stated on the overview. Confirm with LangChain.

## 9. Monitoring and observability

(a) Plain English.
- Tracing: each run of your app is recorded as a trace made of steps ("runs" or spans). You turn it on with environment variables. You can wrap a provider client and mark functions with a decorator.
- Dashboards: charts of trends. Prebuilt dashboards exist per project (traces, LLM calls, cost and tokens, tools, run types, feedback scores). You can build custom charts (count, latency, tokens, cost, feedback score, ratio).
- Alerts: threshold rules on run count, cost, errors, feedback score, or latency, over a 5 or 15 minute window. Channels: Slack, PagerDuty, Dynatrace, webhook.

(b) URLs read:
- https://docs.langchain.com/langsmith/observability-quickstart.md
- https://docs.langchain.com/langsmith/dashboards.md
- https://docs.langchain.com/langsmith/alerts.md
- Index (688 monitor pages): https://docs.langchain.com/_llms/agent-development-lifecycle/monitor.txt, covering tracing for many frameworks, sampling, redaction, bulk export, threads.

(c) Example (fragment, trimmed by the tool):

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_AGENT_ID="<your-agent-id>"
export LANGSMITH_AGENT_ENVIRONMENT="local"
```

```python
client = wrap_openai(OpenAI())

@traceable
def assistant(question: str) -> str:
```

The page says: `pip install -U langsmith openai`. Other variables: `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` (project-based workspaces and self-hosted), `LANGSMITH_ENDPOINT` (outside the US region). The quickstart's Java line is `com.langchain.smith:langsmith-java:0.1.0-beta.27`. Do not mix legacy destination settings with agent addressing.

(d) Check:
- Traces contain prompts and outputs. The index lists pages on masking inputs, redacting secrets, and sampling. Not read. Read them before tracing real user data.
- Metadata and tags do not pass from parent runs to child runs (dashboards page). Add them where you group.
- Dashboard group-by shows the top 20 only. Prebuilt top-N charts show 5.
- Alerts: "Send Test Alert does not validate the downstream response." Check the receiver yourself. Alert filters allow AND only. PagerDuty will not open a new incident if one is still open for the same alert. Self-hosted alerts need Helm chart 0.10.3 or later. Plan availability for alerts is not stated.

## 10. LLM Gateway

(a) Plain English. It is documented. It is a LangSmith feature, not an open source library. You call models from several providers through one endpoint with one LangSmith API key. To switch provider you change the model ID. Every call is traced and your team's spend rules apply. There are 19 pages: admin setup, API formats (Chat Completions, Messages, Responses), direct model access, coding-agent setup, decision models, credits, model configurations, fallbacks, authentication, traces, spend monitoring, spend, rate limit, model access, header, and data policies.

Status: the quickstart says it is in beta. A search result snippet said "private beta" with a waitlist, but the quickstart page I read says only "beta" and needs a paid-plan org. Treat access terms as UNVERIFIED. The changelog lists gateway items (for example "ScaleDown in LLM Gateway", week of Oct 12-19, 2026).

(b) URLs read:
- https://docs.langchain.com/langsmith/llm-gateway-quickstart.md
- Page list from https://docs.langchain.com/_llms/products-and-setup.txt (all under `/langsmith/llm-gateway*.md`)
- Search results also point to a self-hosted guide needing Helm chart 0.17.1 or later (snippet only, not read).

(c) Example (quickstart, shell setup only; I did not see a full request body):

```bash
export LANGSMITH_GATEWAY_BASE_URL="https://gateway.smith.langchain.com/v1"
curl "$LANGSMITH_GATEWAY_BASE_URL/models"
```

Then send a chat completion to `/chat/completions` with a model ID from that list.

(d) Check:
- Beta. Features may change.
- Needs a paid-plan LangSmith organization and a provider key unless the workspace has one.
- Errors: 401 and 403 are authentication, 424 is provider credentials.
- Read the spend, rate-limit, and data policy pages before giving it to a team. Not read.

## 11. Finding and fixing agent issues automatically

Two features exist. They are different.

### 11.1 LangSmith Engine

(a) Plain English. "LangSmith Engine is the LangSmith agent for agent engineering." It reads production traces, finds recurring problems, ranks them by severity, diagnoses them, and can propose a fix as a pull request (or GitLab merge request) for agents built with Deep Agents, LangChain, or LangGraph. It never merges pull requests itself. It attaches new matching traces to open issues, reopens issues that come back, and can turn failing traces into dataset examples for offline evals. Your actions (close, reprioritize) shape later scans. It uses feedback scores as a strong signal.

Setup: enable Engine for the organization, turn it on for a tracing project or agent environment. Connecting GitHub or GitLab is optional but improves diagnosis.

Fix validation (separate feature): marked private beta, LangSmith Cloud only, and only for agents on Cloud deployments. Engine builds a preview deployment from the PR, replays up to five traces against it, and retries a fix up to three attempts. "Inconclusive" means no trustworthy evidence. It does not mean fixed.

(b) URLs read:
- https://docs.langchain.com/langsmith/engine.md
- https://docs.langchain.com/langsmith/engine-issues.md
- https://docs.langchain.com/langsmith/engine-fix-validation.md
- Listed, not read: https://docs.langchain.com/langsmith/engine-repositories.md

(c) Example: no code on the pages I read. UI flow: Engine page, an issue, "Open PR". CLI status values on the issues page: `open`, `fixing`, `watching`, `completed`, `ignored`.

(d) Check:
- Cost: Engine bills in LangChain Standard Units, $1 USD each. A default limit of 750 LSU per month applies until an admin changes it. Analysis level choices: Reduced, Standard, Expanded.
- Plan availability for Engine: not stated on the page.
- Engine itself is not labeled beta. Fix validation and Red Teaming are labeled beta.
- A PR from Engine is a proposal. Review it like any other PR.
- Preview deployments inherit the baseline's secrets. Later secret changes do not reach existing previews.

### 11.2 Insights

(a) Plain English. Insights analyzes traces to find usage patterns, common behavior, and failure modes. It groups traces into categories and subcategories, and gives an executive summary with percentages. It reports. It does not fix anything. The page does not mention auto-fix or Polly.

Run it from the UI (Tracing, "+New", "New Insights Report", up to 30 minutes), the SDK (`client.generate_insights()`), or the CLI (`langsmith insights create --project my-app --config insights.json --wait`). Sample size up to 1,000 traces. Schedules: daily or weekly at 8:00 UTC, or cron in UTC.

(b) URL: https://docs.langchain.com/langsmith/insights.md

(c) Code: only the CLI line above and a call stub `report = client.generate_insights(` (the tool cut off the arguments).

(d) Check: plan is Plus or Enterprise. Cost per the page: about $1.00 to $2.00 per 1,000 threads with OpenAI models, $3.00 to $4.00 with current Anthropic models. Needs a model configuration in the workspace.

### 11.3 LangSmith Chat (formerly Polly)

(a) Plain English. The docs page says "LangSmith Chat (formerly Polly)". It is an assistant inside LangSmith where you ask questions about traces, threads, prompts, and evaluations. It appears in tracing views, Engine, Playground, Prompt Hub, experiments, annotation queues, and the evaluator builder. When you ask, it can edit prompts in the Playground, create datasets from runs, and generate evaluator code. The doc does not say it fixes problems automatically.

(b) URLs read: https://docs.langchain.com/langsmith/chat.md. A search also returned https://docs.langchain.com/langsmith/polly-self-hosted and https://docs.langchain.com/langsmith/self-host-insights-chat (snippets only). The snippet says Insights and Chat are on by default in Helm chart 0.15.1 or later and each needs a Fernet encryption key that should not be rotated. UNVERIFIED, from snippet.

(c) Code: none.

(d) Check: you must add a model provider key as a workspace secret. Calls come from LangSmith egress IPs, so you may need to allowlist them. Beta or GA status, plan, and limits are not stated.

Names not found as official doc pages: "auto-fix" (as a product name). The closest documented thing is the Engine "proposed fix" flow.

## 12. Fleet (extra, from build-overview)

Fleet is a no-code agent builder inside LangSmith with 24 pages (quickstart, templates, channels, schedules, tools, webhooks, access and oversight, and a changelog). I only read the index entries. Not covered further. UNVERIFIED beyond the titles.

## 13. Docs repo and how docs are published (for the docs-watcher)

Repo: https://github.com/langchain-ai/docs. README text: "Unified LangChain documentation". Public, MIT license, default branch `main`. The page showed 5,551 commits, 238 open issues, 97 open PRs.

What the README says it covers:
- docs.langchain.com (LangChain, LangGraph, LangSmith, LangChain Labs), hosted on Mintlify.
- reference.langchain.com (API reference). The README says it is not built from this repo.
- chat.langchain.com (assistant for the docs).

Path layout (top level, from the file listing):
- Directories: `.agents/skills`, `.cursor/rules`, `.github`, `.vscode`, `docs-release-watch`, `openwiki`, `pipeline`, `scripts`, `src`, `tests`.
- Files: `AGENTS.md`, `Makefile`, `README.md`, `LICENSE`, `package.json`, `pyproject.toml`, `packages.yml`, `.vale.ini`, and tooling configs.
- `src/` holds the source. Subfolders: `.mintlify/skills`, `.well-known`, `code-samples`, `fonts`, `images`, `langsmith`, `oss`, `snippets`. Files: `docs.json` (Mintlify navigation), `build-overview.mdx`, `index.mdx`, `use-these-docs.mdx`, `playground.mdx`, and a few `.js` helpers. The listing was truncated, so there may be more.
- URL to path map: `docs.langchain.com/build-overview` edits `src/build-overview.mdx` (the page footer links to `https://github.com/langchain-ai/docs/edit/main/src/build-overview.mdx`). `docs.langchain.com/oss/python/...` lives under `src/oss/`. `docs.langchain.com/langsmith/...` lives under `src/langsmith/`. I did not open a Python page's source to confirm the exact file name pattern (for example one file for both languages). UNVERIFIED.
- `docs-release-watch/` is a managed Deep Agent. It watches releases of OpenWiki, Deep Agents (Python), Deep Agents Code, and Deep Agents JS (Mon/Wed/Fri). For each release published 7 to 30 days ago, it compares source to docs and opens a Linear ticket and a draft PR per feature. This is close to what the course's docs-watcher would do.

Build and publish (README): source is `.mdx` in `src/`. A preprocess step generates `build/`. Mintlify deploys from `build/`. "Never edit `/build` directly." Commands: `make install`, `make dev`, `make build`, `make test`, `make lint`. Checks: Vale (prose style), codespell, htmltest.

Change signals that exist (all fetched and confirmed unless noted):

| Signal | URL | What I saw |
|---|---|---|
| llms.txt index | https://docs.langchain.com/llms.txt | Index of two sub-indexes: AGENT DEVELOPMENT LIFECYCLE (1,481 pages) and PRODUCTS AND SETUP (217 pages). Sub-indexes at `/_llms/*.txt` (build, deploy, monitor, and more). Also lists three OpenAPI specs. |
| Sitemap | https://docs.langchain.com/sitemap.xml | Valid XML sitemap. Every visible entry has a `<lastmod>` timestamp, for example `2026-11-02T19:29:03.492Z`. The file is large (256,209 characters). I read the first 100,000 only. |
| Per-page markdown | append `.md` to a page URL | Returns the page as Markdown. |
| GitHub commit feed | https://github.com/langchain-ai/docs/commits/main.atom | Valid Atom feed. Newest entry seen: 2026-11-02 19:27:05 UTC. |
| LangSmith Cloud changelog | https://docs.langchain.com/langsmith/changelog | Weekly entries, latest seen "October 26-November 2, 2026". |
| Changelog RSS | https://docs.langchain.com/langsmith/changelog/rss.xml | Valid RSS 2.0, titled "LangSmith Cloud changelog". |
| Fleet changelog | https://docs.langchain.com/langsmith/fleet/changelog.md | Listed, not read. |
| Self-hosted changelog | https://docs.langchain.com/langsmith/self-hosted-changelog.md | Listed, not read. |
| Old changelog site | https://changelog.langchain.com/ | 301 redirects to the LangSmith changelog above. |

Not found: a changelog or RSS for LangChain, LangGraph, or Deep Agents library releases on the docs site. The reference overview page lists none. The API reference lives at reference.langchain.com (links to `/python/deepagents`, `/python/langchain`, `/python/langgraph`). Release tracking for those is UNVERIFIED. `https://docs.langchain.com/langsmith/changelog.xml` returned 404.

Most stable URL to poll: `https://docs.langchain.com/sitemap.xml`. It covers all pages and has a per-page `lastmod`. Diff the `lastmod` values, then fetch changed pages with `.md` and diff the text. A cheaper trigger is the GitHub Atom feed `https://github.com/langchain-ai/docs/commits/main.atom`, which shows each commit and its date. Use both: the Atom feed as a wake-up, the sitemap as the truth. Caveat: whether `lastmod` changes only on real content edits or also on rebuilds is UNVERIFIED. In the sample, several unrelated API pages shared the same timestamp minute, which hints that a bulk rebuild can bump many pages. Hash the page text before you report a change.

## 14. Lesson plan

Reader level: college graduate, no jargon. Short lessons. Each lesson ends with one runnable file. All code must be re-copied from the live page and tested before publishing.

### Track A: Agents

A1. Your first agent in 15 lines
- Build a weather agent with `create_agent`. Show the loop: model, tool call, answer.
- Sources: https://docs.langchain.com/oss/python/langchain/overview.md, https://docs.langchain.com/oss/python/langchain/agents.md, https://docs.langchain.com/oss/python/langchain/tools.md

A2. Models and messages without the magic
- Call a model directly, read the four message types, swap providers by changing one string.
- Sources: https://docs.langchain.com/oss/python/langchain/models.md, https://docs.langchain.com/oss/python/langchain/messages.md

A3. Make the agent answer in a fixed shape
- Use `response_format` to get a typed result. Show what happens when validation fails.
- Sources: https://docs.langchain.com/oss/python/langchain/structured-output.md

A4. RAG from local to a real store
- Load, split, embed, store, retrieve. Start in memory, then swap the vector store using the integrations table.
- Sources: https://docs.langchain.com/oss/python/langchain/knowledge-base.md, https://docs.langchain.com/oss/python/integrations/vectorstores/index.md, https://docs.langchain.com/oss/python/integrations/document_loaders/index.md

A5. Guardrails with middleware
- Add retries, summarizing, and a call limit. Explain hooks in plain words.
- Sources: https://docs.langchain.com/oss/python/langchain/middleware/overview.md, .../middleware/built-in.md, .../middleware/custom.md (last two to read)

A6. Pause for a human
- Require approval before a risky tool. Cover checkpointer, `thread_id`, approve and reject.
- Sources: https://docs.langchain.com/oss/python/langchain/human-in-the-loop.md, https://docs.langchain.com/oss/python/langgraph/interrupts.md

A7. State, nodes, edges: LangGraph by hand
- Build a three-node graph with a reducer. Add a Postgres checkpointer. Show a resume after a crash.
- Sources: https://docs.langchain.com/oss/python/langgraph/graph-api.md, .../persistence.md, .../durable-execution (read the real page first)

A8. Deep agents: planning, files, helpers
- Build a research agent with a todo list, a file backend, and one subagent. Cover backend safety.
- Sources: https://docs.langchain.com/oss/python/deepagents/overview.md, .../subagents.md, .../backends.md

A9. RAG with a deep agent
- Retrieve, write chunks to files, let subagents read them. Cover prompt injection.
- Sources: https://docs.langchain.com/oss/python/deepagents/rag.md

A10. Managed deep agents (public beta)
- Scaffold with `mda init`, run with `mda dev`, deploy with `mda deploy`. State the beta label up front.
- Sources: https://docs.langchain.com/langsmith/python/managed-deep-agents-overview.md, .../managed-deep-agents-quickstart.md

A11. A wiki for your agent: OpenWiki
- Generate `openwiki/` for a repo. Review the diff. Optional CI refresh.
- Sources: https://docs.langchain.com/oss/openwiki/overview.md, .../quickstart.md, .../automate-updates.md

### Track B: Evals and refining

B1. Why test an agent
- Dataset, example, experiment, evaluator, offline vs online, in plain words with one diagram.
- Sources: https://docs.langchain.com/langsmith/evaluation-concepts.md, https://docs.langchain.com/langsmith/evaluation.md

B2. Your first offline eval
- Make a small dataset, a target function, a code evaluator, run `evaluate`, read the experiment.
- Sources: https://docs.langchain.com/langsmith/evaluate-llm-application.md, https://docs.langchain.com/langsmith/analyze-an-experiment.md

B3. Judges and their limits
- Add an LLM-as-judge. Audit its scores against human labels.
- Sources: https://docs.langchain.com/langsmith/llm-as-judge.md, https://docs.langchain.com/langsmith/audit-evaluator-scores.md

B4. Evaluate a RAG app and an agent's steps
- Score retrieval and final answers. Score tool-call trajectories.
- Sources: https://docs.langchain.com/langsmith/evaluate-rag-tutorial.md, https://docs.langchain.com/langsmith/trajectory-evals.md

B5. Refine a prompt with evidence
- Edit in the Playground, commit, tag, rerun the experiment, compare.
- Sources: https://docs.langchain.com/langsmith/prompt-engineering-quickstart.md, https://docs.langchain.com/langsmith/compare-experiment-results.md, https://docs.langchain.com/langsmith/chat.md

B6. Online evals on live traffic
- Add a sampled judge with filters. Watch cost and the weekly limit. Backfill once.
- Sources: https://docs.langchain.com/langsmith/online-evaluations-llm-as-judge.md

B7. Close the loop with Engine
- Let Engine find an issue, review its PR, add failing traces to a dataset. Fix validation is private beta.
- Sources: https://docs.langchain.com/langsmith/engine.md, .../engine-issues.md, .../engine-fix-validation.md

### Track C: Deploy and monitor

C1. Turn on tracing
- Three env vars and one decorator. Read a trace. Add metadata and tags.
- Sources: https://docs.langchain.com/langsmith/observability-quickstart.md, https://docs.langchain.com/langsmith/add-metadata-tags.md (to read)

C2. Keep secrets out of traces
- Mask inputs, redact secrets, sample.
- Sources: https://docs.langchain.com/langsmith/mask-inputs-outputs.md, .../redact-secrets.md, .../sample-traces.md (all to read)

C3. Dashboards and alerts
- Read the prebuilt dashboard. Build one error-rate chart. Add a Slack alert and test it.
- Sources: https://docs.langchain.com/langsmith/dashboards.md, https://docs.langchain.com/langsmith/alerts.md

C4. Find patterns with Insights
- Run a report on 200 traces. Read the categories. Mind the cost.
- Sources: https://docs.langchain.com/langsmith/insights.md

C5. Deploy to LangSmith Cloud
- Run `langgraph dev`, then deploy. Serverless vs dedicated.
- Sources: https://docs.langchain.com/langsmith/deploy-to-cloud-overview.md, https://docs.langchain.com/langsmith/agent-server-overview.md

C6. Self-host choices
- Full, hybrid, standalone. Postgres and Redis. What you now own.
- Sources: https://docs.langchain.com/langsmith/deploy-to-self-hosted-overview.md, https://docs.langchain.com/langsmith/deploy-standalone-server.md

C7. One door for many models: LLM Gateway (beta)
- Send a request, view the trace, set a spend rule.
- Sources: https://docs.langchain.com/langsmith/llm-gateway-quickstart.md, .../llm-gateway-spend-policies.md (to read)

C8. Watching the docs for changes
- Poll the sitemap, diff `lastmod`, hash page text, use the Atom feed as a trigger.
- Sources: https://docs.langchain.com/sitemap.xml, https://github.com/langchain-ai/docs/commits/main.atom, https://github.com/langchain-ai/docs/tree/main/docs-release-watch

## 15. What I could not verify

- Deep Agents install command. The overview page gave none.
- The exact minimal Deep Agents code. The fetch tool did not quote it. Copy from the page.
- LangGraph durable execution page. Both URLs I tried showed the Persistence page. Durability modes ("exit", "async", "sync"), task wrapping, and `langgraph>=1.2` graceful shutdown come only from a search-result snippet.
- Agent Server CLI install command, `langgraph.json` format, and the `langgraph deploy` flags. Not on pages I read.
- Whether LangGraph, LangChain, and Deep Agents library releases have a changelog or feed on the docs site. I found none.
- Whether sitemap `lastmod` moves only on real edits. Only 100,000 of 256,209 characters were read. Total URL count unknown.
- Exact source file path pattern for Python vs JavaScript pages under `src/oss/`. The `src/` listing was cut off.
- Plan and price for Managed Deep Agents, Engine, LangSmith Chat, alerts. Not stated on the pages read.
- LLM Gateway access terms. The quickstart says "beta". A search snippet said "private beta" with a waitlist. Not reconciled.
- LLM Gateway request body and spend-policy details. Not read.
- Polly self-hosting details (Helm 0.15.1, Fernet key). Snippets only.
- Pages listed but not read: middleware built-in and custom, event streaming, dynamic and async subagents, Deep Agents retrieval, most OpenWiki pages (cli-reference, customize, providers, code-mode, personal-mode), the 24 Fleet pages, evaluation pages beyond the five read, Engine repositories, data and privacy pages, hybrid and control-plane deploy pages.
- Author or maintainer and version of OpenWiki. The docs pages name neither.
- A product called "auto-fix". Not found by that name. Engine's "proposed fix" is the nearest documented feature.
- All code snippets: they pass through a summarizing fetch tool. Several were trimmed or rewritten by it, and I marked those. Re-copy from the live pages and run them.

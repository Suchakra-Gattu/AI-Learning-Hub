---
title: ai-engineering-hub: project map
summary: All the projects in the ai-engineering-hub repo grouped by topic, the best starters, and gaps.
time: 30 min
---


Source: https://github.com/patchy631/ai-engineering-hub (shallow clone, last commit dated 2026-10-30). I read the root README and the README of each project folder. I did not run or install any code.

## 1. Overview

- The hub is a collection of small, separate demo projects. Each folder is its own app with its own README. There is no shared package.
- The root README says "93+ projects" and sorts them into Beginner (22), Intermediate (48) and Advanced (23). The clone has 117 top-level folders: 114 projects, plus `assets`, `resources` (images only) and `courses` (a link list).
- 21 projects are newer than the root README list. They have no tier there. I marked their difficulty "est." (my guess).
- The root README links two projects that are not in the clone: `attention-is-all-you-need-impl` and `nvidia-demo`.
- 9 folders have no README at all (just code or notebooks). They are marked "None" below.
- Style: most projects are "tools X + Y + Z, plus a UI". Typical pattern is Streamlit or Chainlit front end, Ollama for local models, and a hosted vendor (Firecrawl, Bright Data, AssemblyAI, Zep, Opik) for one feature. Many READMEs are short and mainly list setup steps and API keys. Few explain the idea behind the build.
- The hub is organized by tool, not by lesson. Many projects repeat the same idea with a different vendor (about 20 are chat-with-docs RAG, 8 are model-vs-model comparisons).
- Strongest parts: RAG variants, MCP servers, CrewAI agents, voice demos, Opik-based model comparison.
- Weakest parts: no deployment beyond a few demos, little on testing, no cost tracking, no safety work except one guide.

## 2. All projects

Difficulty is the repo's own tier (B/I/A) unless marked "est.". "README" says whether the README alone is enough to learn from: Good = explains what and how; Setup = mostly setup steps and keys, concept is thin; None = no README.

| Project | Topic | Tools | What it teaches | Diff. | README |
|---|---|---|---|---|---|
| acp-code | Agents | Agent Communication Protocol, CrewAI, Smolagents, Ollama | Two agents built with different tools work together through one shared protocol | I (est.) | Setup |
| agent2agent-demo | Agents | Python files and a notebook (not read in depth) | Agent-to-agent calls demo | est. I | None |
| agent-with-mcp-memory | Agents, MCP, observability | CrewAI, Graphiti, MCP, Opik | Crash course: what an agent is, tools, MCP servers, tracing | I | Good |
| agentic_rag | RAG, agents | CrewAI, Qdrant, Firecrawl, chonkie, fastembed | Search your docs first, fall back to the web if no answer | I | Setup |
| agentic_rag_deepseek | RAG, agents | CrewAI, GroundX, DeepSeek | Agent that reads hard documents (tables, figures) through a parsing service | I | Setup |
| ai_news_generator | Agents | CrewAI, Cohere, Serper | Two agents research a topic and write a news post | B | Setup |
| ai-avatar-demo | Voice, memory | Zep, Anam AI avatar, OpenRouter, FastAPI, Streamlit | Talking avatar that remembers past chats | est. A | Good |
| ai-engineering-roadmap | Learning guide | Link list | Study path from Python to production AI | B | Good |
| ai-podcast-generation | Voice, multimodal | OpenAI or Ollama, Streamlit | Turn web text into a two-speaker podcast, cloud or local | est. I | Good |
| ai-podcast-generator | Voice, multimodal | Minimax M2.1, Minimax Speech, Firecrawl, Streamlit | Article to podcast script to audio to merged file | est. I | Good |
| amazon-product-analysis-server | MCP | mcp-use, Bright Data, React widget | Build an MCP server with a small interactive widget | est. A | Good |
| art_mcp_rl | Fine-tuning, MCP, agents | OpenPipe ART, GRPO, RULER, FastMCP, SQLite, Qwen 2.5 3B | Train a small model with reinforcement learning to use database tools | est. A | Good |
| audio-analysis-toolkit | Voice, MCP | AssemblyAI, Streamlit, Cursor | Transcribe and analyze audio, reachable from an MCP host | I | Setup |
| autogen-stock-analyst | Agents | AutoGen, Qualcomm Cloud AI 100 | Agents write and run code to analyze stocks | I | Setup |
| biotech-agentic-analyst | Agents, multimodal | CrewAI, Mistral OCR 4, Streamlit | Pull figures out of science PDFs, then agents summarize each one | est. I | Good |
| book-writer-flow | Agents | CrewAI, Gemma 3, Bright Data | A chain of agents that writes a book from web research | I | Setup |
| brand-monitoring | Agents | CrewAI, DeepSeek-R1, Bright Data | Agents scan the web for mentions of a brand | I | Setup |
| build-code-harness | Harness, agents | CrewAI, E2B sandbox, OpenRouter | Rebuild a coding-agent harness: planning, memory, checkpoints, sandbox, human approval | est. A | Good |
| Build-reasoning-model | Fine-tuning | Unsloth, vLLM | Build a DeepSeek-R1 style reasoning model | A | Thin |
| chat-with-audios | RAG, voice | AssemblyAI, LlamaIndex, Qdrant, Streamlit | Ask questions over audio files by transcribing first | I | Setup |
| chat-with-code | RAG | LlamaIndex, Milvus, Cleanlab Codex, OpenRouter (Qwen3-Coder) | Ask questions about a code repo with an answer-quality check | I | Setup |
| code-model-comparison | Evals | LiteLLM, Opik, Gitingest, Streamlit | Compare coding models with scored judging | I | Setup |
| colbert-rag | RAG | `colbert.py` only | Late-interaction retrieval (from file name only) | est. A | None |
| Colivara-deepseek-website-RAG | RAG, multimodal | ColiVara, Janus-Pro, Firecrawl, Streamlit | Search websites as page images, not text | I | Setup |
| content_planner_flow | Agents | CrewAI Flow, Llama 3.2, Firecrawl, Typefully | Scrape a site, draft a post, publish it | I | Setup |
| context-engineering-pipeline | Agents, RAG | Pixeltable, sentence transformers, MCP | Mix chat history, retrieved text and memory inside a token budget | est. A | Good |
| context-engineering-workflow | Agents, RAG | CrewAI Flows, TensorLake, Voyage, Milvus, Zep | Research assistant that combines document search, memory and web | A | Good |
| conversational-support-flow | Agents | CrewAI, AG-UI, CopilotKit, OpenRouter, Exa, Next.js | Support bot where a router picks: order lookup, doc answer, or web search | est. A | Good |
| corrective-rag | RAG | `app.py`, `workflow.py` | Corrective RAG (from file names only) | est. I | None |
| courses | Learning guide | Link list | Links to 13 free Anthropic courses | B | Good |
| cursor_linkup_mcp | MCP | Linkup, LlamaIndex, Cursor | Your own MCP server that gives an IDE web search | I | Setup |
| database-memory-agent | Agents, RAG | MongoDB Atlas Vector Search, Voyage AI, OpenAI | Agent that stores and recalls memory in a database | est. I | Good |
| DeepSeek-finetuning | Fine-tuning | Unsloth, Ollama | Fine-tune a small DeepSeek model and run it locally | A | Thin |
| deepseek-multimodal-RAG | RAG, multimodal | Janus-Pro, ColPali, Qdrant, Streamlit | RAG over images and PDFs | I | Setup |
| deepseek-thinking-ui | Other (chat UI) | DeepSeek-R1, Ollama, Streamlit | Show the model's reasoning in a chat app | B | Thin |
| deploy-agentic-rag | Deployment | CrewAI, LitServe, Ollama (Qwen3) | Wrap an agent as a private API | I | Thin |
| documentation-writer-flow | Agents, MCP | CrewAI, DeepSeek-R1, Ollama, Cursor | Agents write docs for your code | A | Setup |
| document-chat-rag | RAG | Llama 3.3, Qdrant, Streamlit | Basic chat with your documents, local | B | Setup |
| eval-and-observability | Evals, observability | Opik, notebooks | End-to-end scoring and tracing of a RAG app | I | Thin |
| eyelevel-mcp-rag | MCP, RAG | GroundX | MCP server for RAG over hard documents | I | Thin |
| fastest-rag-milvus-groq | RAG, deployment | LlamaIndex, Milvus (binary vectors), Groq, Beam | Quick retrieval using compressed vectors and fast hosting | I | Good |
| fastest-rag-stack | RAG | SambaNova, LlamaIndex, Qdrant, Streamlit | Basic RAG with a fast hosted model | B | Setup |
| financial-analyst-deepseek | MCP, agents | CrewAI, DeepSeek-R1, Cursor | Stock-analysis agents behind an MCP server | A | Setup |
| finetune-studio-mcp-app | LLMOps, fine-tuning, MCP | Hugging Face AutoTrain, Gradio, Manufact MCP Cloud | Fine-tune a model from inside Claude through an MCP app | est. A | Good |
| firecrawl-agent | RAG, agents | LlamaIndex, Firecrawl, Milvus, Streamlit | Corrective RAG: web search when documents fall short | A | Good |
| flight-booking-crew | Agents | `app.py`, `browserbase.py`, `kayak.py` | Flight search crew (from file names only) | est. I | None |
| gemma3-ocr | Multimodal | Gemma 3, Ollama, Streamlit | Read text from images locally | B | Thin |
| github-rag | RAG | GitIngest, LlamaIndex | Chat with a GitHub repo | B | Setup |
| gpt-oss-thinking-ui | Other (chat UI) | GPT-OSS 20B, Ollama | Local chat that shows reasoning | B | Good |
| gpt-oss-vs-qwen3 | Evals | LiteLLM, Opik G-Eval, OpenRouter | Judge two reasoning models side by side | I | Setup |
| graphiti-mcp | MCP, memory | Graphiti (Zep), Cursor, Claude | One memory shared by several AI clients | A | Setup |
| groundX-doc-pipeline | RAG | GroundX, Ollama, Streamlit | Parse documents with tables and figures | A | Setup |
| grpo-finetuning-qwen3 | Fine-tuning, evals | Fireworks Training API, GRPO, Qwen3-8B, OpenRouter | Train a small model to extract invoice JSON; README reports 82% vs 62% base and 58% GPT-4.1 | est. A | Good |
| guidelines-vs-traditional-prompt | Agents | Parlant | Structured rules versus one big prompt, tested on 5 insurance questions | A | Good |
| hotel-booking-crew | Agents | CrewAI, DeepSeek-R1, Browserbase | Agents use a headless browser to find hotels | I | Setup |
| hugging-face-skills | Harness | Agent Skills format, Bright Data | What a SKILL.md folder is and how agents use it | est. I | Good |
| imagegen-janus-pro | Multimodal | Janus-Pro 7B, Streamlit | Local image generation and image Q and A | B | Thin |
| kitops-mcp | LLMOps, MCP | KitOps ModelKits | Package and share ML models like containers | I | Good |
| knowledge distillation | Fine-tuning | One notebook | Teach a small model from a big one (from file name only) | est. A | None |
| LaTeX-OCR-with-Llama | Multimodal | Llama 3.2 vision, Streamlit | Turn equation images into LaTeX | B | Thin |
| llama-4_vs_deepseek-r1 | Evals, RAG | LlamaIndex, Opik, Groq | Compare two models on the same RAG app | I | Setup |
| llama-4-rag | RAG | LlamaIndex, Llama 4, Cerebras | Basic RAG with Llama 4 | B | Thin |
| llamaindex-mcp | MCP | LlamaIndex, SQLite MCP server | Build a local MCP client | I | Thin |
| llama-ocr | Multimodal | Llama 3.2 vision, Streamlit | Local OCR app | B | Thin |
| local-chatgpt with DeepSeek | Other (chat UI) | Chainlit, DeepSeek-R1, Ollama | Local chat app | B | Thin |
| local-chatgpt with Gemma 3 | Other (chat UI) | Chainlit, Gemma 3, Ollama | Local chat app | B | Thin |
| local-chatgpt | Other (chat UI) | Chainlit, Llama 3.2 vision, Ollama | Local chat app | B | Thin |
| mcp-agentic-rag | MCP, RAG | Bright Data, Qdrant, Cursor | Agentic RAG exposed as MCP tools | I | Setup (intro text looks copied from another project) |
| mcp-agentic-rag-firecrawl | MCP, RAG | Firecrawl, Qdrant, Cursor | Same idea with Firecrawl | I | Setup |
| mcp-video-rag | MCP, multimodal | Ragie, Cursor | Ask questions about videos over MCP | I | Setup |
| mcp-voice-agent | Voice, MCP | AssemblyAI, Firecrawl, Supabase | Voice agent that searches the web and writes to a database | I | Good |
| mindsdb-mcp | MCP | MindsDB, Cursor | One MCP server in front of many data sources | A | Good |
| minimaxm2-vs-sonnet4-5-vs-kimik2-vs-gemini3 | Evals | LiteLLM, Opik G-Eval, OpenRouter, Gitingest | Score four coding models on a repo | est. I | Good |
| modernbert-rag | RAG | ModernBERT embeddings, Llama 3.2, Streamlit | Swap the embedding model in a basic RAG app | B | Thin |
| motia-content-creation | Agents | Motia, Firecrawl, Ollama | Article to Twitter and LinkedIn posts | I | Good |
| Multi-Agent-deep-researcher-mcp-windows-linux | Agents, MCP | Linkup, CrewAI, DeepSeek-R1 | Deep-research agents behind MCP | A | Setup |
| multilingual-meeting-notes-generator | Voice | AssemblyAI, an LLM | Detect language, transcribe, label speakers, summarize | I | Good |
| multi-modal-rag | RAG, multimodal | Two notebooks (CLIP, multimodal prompting) | Image-text retrieval (from file names only) | est. I | None |
| multimodal-rag-assemblyai | RAG, voice | CrewAI Flows, AssemblyAI, Milvus, OpenAI | Audio to text to vectors to answers | I | Setup |
| multiplatform_deep_researcher | Agents, MCP | Bright Data MCP, CrewAI, Ollama | Deep research across many sites | A | Setup |
| notebook-lm-clone | RAG, multimodal | Mixed (docs, audio, YouTube, web) | Full app with cited answers and podcast output | A | Good |
| o3-vs-claude-code | Evals | Opik, LlamaIndex | Compare two models on code RAG | I | Setup |
| omnigraph-multi-agent | Agents, memory | Graph schema and data files | Two agents share a graph (from file names only) | est. A | None |
| open-agent-builder | Agents, harness | Composio, drag-and-drop nodes | Visual workflow builder with approval and loop nodes | est. A | Good |
| openai-swarm-ollama | Agents | Swarm, Ollama | Multi-agent demo (from file names only) | est. I | None |
| openclaw-secure-deployment | Deploy | DigitalOcean, Tailscale, SSH, firewall | Lock down a server that runs an agent | est. I | Good |
| paralegal-agent-crew | Agents, RAG | CrewAI, Milvus, Firecrawl | Legal-document Q and A with web fallback | A | Setup |
| parlant-conversational-agent | Agents | Parlant | Loan flow with fixed steps and rules | A | Good |
| pixeltable-mcp | MCP, multimodal | Pixeltable, router and specialist agents | Route text, image, video and audio questions to the right agent | A | Good |
| qwen-2.5VL-ocr | Multimodal | Qwen 2.5 VL, Streamlit | OCR and text finding with boxes; README says work in progress | B | Thin |
| qwen3_vs_deepseek-r1 | Evals, RAG | LlamaIndex, Opik, Ollama | Compare two models | I | Setup |
| qwen3-thinking-ui | Other (chat UI) | Qwen3 4B, Streamlit | Thinking display | B | Thin |
| rag-sql-router | RAG, agents | LlamaIndex, SQL, Cleanlab Codex | Agent that picks between a document index and a SQL query | I | Good |
| rag-voice-agent | Voice, RAG | Cartesia, OpenAI or other STT | Talk to your documents in real time | I | Good |
| rag-with-dockling | RAG | LlamaIndex, Docling, Qwen3 | RAG over Excel and slides | I | Thin |
| real-time-voicebot | Voice | AssemblyAI, ElevenLabs, OpenAI | Live speech in, speech out travel guide | I | Good |
| resources | (images only) | none | none | n/a | n/a |
| run-jev-inside-agent-harness | Harness, cost | Jev decision model (TypeSafe AI), open harness | Where agent tokens go; three levers: context, calls, assignment | est. A | Good |
| sales-analytics-agent | Agents | MindsDB, MongoDB, HubSpot, Docker | SQL across two systems plus an agent | est. I | Good |
| sdv-mcp | MCP | Synthetic Data Vault, Cursor | Make fake tabular data through MCP | I | Thin |
| siamese-network | Other (classic ML) | Notebook, MNIST | Compare two images | B | Thin |
| simple-rag-workflow | RAG | LlamaIndex, Ollama | Smallest RAG example | B | Thin |
| sonnet4-vs-o4 | Evals | LiteLLM, DeepEval, Gitingest | Compare two coding models | I | Setup |
| sonnet4-vs-qwen3-coder | Evals | LiteLLM, DeepEval, Gitingest | Compare two coding models | I | Setup |
| stagehand x mcp-use | MCP, agents | mcp-use, Stagehand, Ollama | Chat that drives a browser | I | Setup |
| stock-portfolio-analysis-agent | Agents | CrewAI, FastAPI, Next.js, CopilotKit, AG-UI | Stream agent steps live into a web UI | A | Good |
| streaming-ai-chatbot | Deployment, other | Motia, OpenAI streaming | Stream tokens and keep chat state | B | Good |
| train-yolo26-object-detection | Fine-tuning (vision) | Ultralytics YOLO26, Roboflow, Comet ML | Train an object detector on your data, track runs | est. I | Good |
| trustworthy-rag | RAG, evals | LlamaParse, Cleanlab TLM | Confidence score on each answer | I | Setup |
| ultimate-ai-assitant-using-mcp | MCP | mcp-use, Stagehand, Firecrawl, Ragie | One chat window over several MCP servers | A | Good |
| video-rag-gemini | Multimodal, RAG | Gemini, Streamlit | Chat with uploaded video | B | Good |
| web-browsing-agent | Agents | CrewAI, Stagehand | Planner, browser and writer agents | A | Good |
| Website-to-API-with-FireCrawl | Other | Firecrawl, Streamlit | Turn a site into structured data | B | Setup |
| Youtube-trend-analysis | Agents | CrewAI, Bright Data | Summarize video transcripts for trends | I | Setup |
| zep-memory-assistant | Agents, memory | Zep, AutoGen, Ollama, Qwen3 | Long-term memory for an agent | I | Setup |
| zep-observations | Memory | Zep | How a memory graph spots patterns across 3 chats | est. A | Good |

Counts: 114 projects plus the 3 non-project folders listed. Topic counts (primary, rough): RAG about 25, agents about 28, MCP about 17, voice about 8, evals about 9, fine-tuning about 6, multimodal and OCR about 12, deployment about 3.

## 3. Projects by our planned tracks

**Foundations**
- ai-engineering-roadmap (study path)
- courses (Anthropic Academy links)
- agent-with-mcp-memory (what an agent is)
- simple-rag-workflow, local-chatgpt, deepseek-thinking-ui, qwen3-thinking-ui, gpt-oss-thinking-ui (run a local model, show reasoning)
- streaming-ai-chatbot (streaming)
- siamese-network (classic ML, optional)

**RAG**
- Basics: simple-rag-workflow, document-chat-rag, fastest-rag-stack, github-rag, llama-4-rag, modernbert-rag
- Better parsing and retrieval: rag-with-dockling, groundX-doc-pipeline, trustworthy-rag, fastest-rag-milvus-groq, colbert-rag (no README)
- Agentic and corrective: agentic_rag, firecrawl-agent, paralegal-agent-crew, rag-sql-router, chat-with-code, corrective-rag (no README)
- Multimodal: deepseek-multimodal-RAG, Colivara-deepseek-website-RAG, video-rag-gemini, multi-modal-rag (no README), notebook-lm-clone
- Memory as retrieval: database-memory-agent, context-engineering-pipeline, context-engineering-workflow

**Agents**
- CrewAI flows: ai_news_generator, content_planner_flow, book-writer-flow, brand-monitoring, Youtube-trend-analysis, hotel-booking-crew, web-browsing-agent, biotech-agentic-analyst
- Other frameworks: autogen-stock-analyst, acp-code, agent2agent-demo, openai-swarm-ollama, motia-content-creation
- Memory: zep-memory-assistant, zep-observations, graphiti-mcp, omnigraph-multi-agent
- MCP: cursor_linkup_mcp, llamaindex-mcp, mcp-agentic-rag, mcp-agentic-rag-firecrawl, eyelevel-mcp-rag, mindsdb-mcp, pixeltable-mcp, sdv-mcp, stagehand x mcp-use, ultimate-ai-assitant-using-mcp, amazon-product-analysis-server, multiplatform_deep_researcher, Multi-Agent-deep-researcher-mcp-windows-linux, financial-analyst-deepseek, documentation-writer-flow
- Rules-based agents: parlant-conversational-agent, guidelines-vs-traditional-prompt, conversational-support-flow
- UI for agents: stock-portfolio-analysis-agent, open-agent-builder

**Harness** (the loop around the model: tools, context, approval, sandbox)
- build-code-harness
- run-jev-inside-agent-harness
- hugging-face-skills
- open-agent-builder
- context-engineering-pipeline and context-engineering-workflow

**Evals**
- eval-and-observability
- code-model-comparison, gpt-oss-vs-qwen3, minimaxm2-vs-sonnet4-5-vs-kimik2-vs-gemini3 (Opik G-Eval)
- sonnet4-vs-o4, sonnet4-vs-qwen3-coder (DeepEval)
- llama-4_vs_deepseek-r1, qwen3_vs_deepseek-r1, o3-vs-claude-code
- trustworthy-rag (answer confidence)
- grpo-finetuning-qwen3 (held-out eval)

**Deploy and monitor**
- deploy-agentic-rag (LitServe API)
- fastest-rag-milvus-groq (Beam hosting)
- openclaw-secure-deployment (server hardening)
- eval-and-observability, agent-with-mcp-memory (Opik tracing)
- streaming-ai-chatbot
- finetune-studio-mcp-app (Manufact MCP Cloud, README says it has logs and metrics)

**Voice AI**
- real-time-voicebot, rag-voice-agent, mcp-voice-agent
- chat-with-audios, audio-analysis-toolkit, multilingual-meeting-notes-generator, multimodal-rag-assemblyai
- ai-podcast-generation, ai-podcast-generator, ai-avatar-demo

**LLMOps and fine-tuning**
- DeepSeek-finetuning, Build-reasoning-model, grpo-finetuning-qwen3, art_mcp_rl
- finetune-studio-mcp-app, kitops-mcp
- train-yolo26-object-detection, knowledge distillation (no README)

**Inference and edge**
- Local models with Ollama: local-chatgpt (3 variants), document-chat-rag, llama-ocr, gemma3-ocr, imagegen-janus-pro
- Fast hosted inference: fastest-rag-stack (SambaNova), fastest-rag-milvus-groq (Groq), llama-4-rag (Cerebras)
- Hardware: autogen-stock-analyst (Qualcomm Cloud AI 100)
- Cost angle: run-jev-inside-agent-harness

## 4. Best starter projects (13)

1. **simple-rag-workflow**: smallest RAG example (LlamaIndex plus Ollama). Good first lesson. README is short, so we must add the explanation.
2. **agent-with-mcp-memory**: one of the few READMEs that explains what an agent is, tools, MCP and tracing in order. Fits Foundations and Agents.
3. **agentic_rag**: shows "search docs, else search the web". Good bridge from RAG to agents.
4. **firecrawl-agent**: corrective RAG with a clear feature list and Milvus. Second step after agentic_rag.
5. **rag-sql-router**: teaches routing between a document index and SQL, plus answer checking. Good for the idea that one question may need different tools.
6. **eval-and-observability**: the only project built to score and trace a RAG app. README is thin, so use the notebooks (not read in depth) as a base, and verify before use.
7. **gpt-oss-vs-qwen3** (or code-model-comparison): shows how to judge two models with a scoring method. Plain, repeatable pattern; the other comparison projects repeat it.
8. **build-code-harness**: rebuilds a coding agent with planning, memory, checkpoints, sandbox and human approval. Best match for the Harness track.
9. **run-jev-inside-agent-harness**: explains where agent cost comes from (context, calls, model choice). It is built around one vendor model, so teach the cost idea and skip the vendor.
10. **real-time-voicebot**: complete speech-in, speech-out loop with a good README. Voice AI starter.
11. **rag-voice-agent**: adds retrieval to a voice agent. Natural second voice lesson.
12. **grpo-finetuning-qwen3**: clear task (invoice JSON), measured result against baselines, and a held-out eval. Best fine-tuning story with a before and after number.
13. **deploy-agentic-rag** plus **openclaw-secure-deployment**: one wraps an agent as an API, the other covers server hardening and execution policies. Together they cover Deploy basics. deploy-agentic-rag README is thin, so we add the missing steps.

Runners-up: parlant-conversational-agent (rules for agents), kitops-mcp (packaging models), notebook-lm-clone (capstone), art_mcp_rl (advanced).

## 5. Gaps: hub topics with no place in our plan

- **MCP as its own topic.** About 17 projects build MCP servers or clients. Our track list has no MCP slot. It could sit inside Agents or Harness.
- **Agent memory.** Zep, Graphiti, database memory, Pixeltable (about 8 projects). Could sit in Agents, but it is a lesson on its own.
- **OCR and vision tasks.** Llama, Gemma, Qwen OCR and YOLO training. Not in our plan except as multimodal RAG.
- **Document parsing.** Docling, GroundX, LlamaParse, TensorLake, Mistral OCR. This is part of RAG but needs its own lesson.
- **Agent UIs and streaming** (AG-UI, CopilotKit, Next.js, Motia). Front-end work; our plan has no UI lesson.
- **Visual agent builders** (open-agent-builder) and **rules-based agents** (Parlant).
- **Synthetic data** (sdv-mcp).
- **Reasoning display and local thinking models.**
- **Reinforcement learning for agents** (art_mcp_rl, grpo-finetuning-qwen3). Beyond plain fine-tuning.
- **Agent protocols** (ACP, agent2agent).
- **Agent skills format** (hugging-face-skills).
- **Classic ML** (siamese-network). Probably out of scope.

Missing from the hub (our plan has a slot, the hub has little): cost tracking, safety and guardrails (only openclaw-secure-deployment), CI tests for AI apps, scaling and load tests, edge or on-device deployment (nothing found), and prompt versioning.

## 6. Licensing and how to reference

- The root `LICENSE` is MIT, copyright 2024 patchy631. The README says the repo is MIT.
- MIT allows reuse if the copyright and license notice are kept. Still, our rule: link, do not copy. Link to the folder, for example `https://github.com/patchy631/ai-engineering-hub/tree/main/<folder>`, and describe it in our own words. Do not paste their README text, code or images.
- Pin links to a commit hash for stability. Folder names can change or vanish (two folders in the root README are already missing).
- One nested file has its own license: `kitops-mcp/ml-project/docs/LICENSE`. I did not read it. Check before reusing anything from that folder.
- Third-party services in the demos (Firecrawl, Bright Data, GroundX and others) have their own terms and keys. The repo license does not cover them.
- Several READMEs carry affiliate-style links and newsletter promotion. Do not copy those links.

## 7. What I could not verify

- I did not run any project. I do not know which ones still work with current library versions.
- Library lists come from READMEs, not from lock files. Projects may use other libraries.
- I did not read the code or notebooks. Projects with no README are classified from file names only.
- Difficulty is the repo's tier for the 93 listed projects. For the 21 others I guessed (marked "est.").
- Many READMEs were read only in the first lines. For the long ones (finetune-studio-mcp-app, mindsdb-mcp, run-jev-inside-agent-harness, notebook-lm-clone) I read the top, not the whole.
- Claims in READMEs (82% vs 62%, "sub-15ms retrieval", "40x to 200x faster") are the authors' claims. I did not check them.
- I did not check if the root README count "93+" matches its own list beyond the tier counts it states.
- I did not read the 13 Anthropic course pages, only the repo's short list.
- Topic and "teaches" lines are my reading of the README, not a test of the project.

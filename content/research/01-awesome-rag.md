---
title: Awesome-RAG, reading map and gaps
summary: What the Awesome-RAG list contains, the best sources by topic, and what we could not verify.
time: 20 min
---


Source: https://github.com/Danielskry/Awesome-RAG (cloned, shallow, read only). Research date: 2026-11-03.
Rule used here: only facts I read are stated as facts. Memory-based items are marked "(unverified)".

## 1. What the repo is and how it is organized

It is a link list, not a course. Its own words: "a curated resource map of tools, frameworks, techniques, and learning materials" for RAG. License is CC0. It has one 507-line README plus two side docs (`docs/python-ecosystem.md`, `docs/supabase-integration.md`). It also points to an agent plugin repo for VS Code, Copilot CLI and Claude Code.

README sections, in order:

1. General Information on RAG (Python tutorials, production guides)
2. Architecture Patterns (naive, advanced, modular, agentic, self, graph, reasoning-based RAG; one line each, no links)
3. Advanced Approaches (about 22 links: Vision-RAG, CAG, Agentic RAG, CRAG, RAFT, Self-RAG, RAG Fusion, GraphRAG, GNN-RAG, Multimodal RAG, VideoRAG, REFRAG, PageIndex and others)
4. Frameworks (LangChain, LlamaIndex, Haystack, Dify, LiteLLM and others)
5. Python Ecosystem (points to the side doc: SDKs, PDF parsers, vector DB clients, async tools)
6. Techniques: data cleaning, prompting, chunking (6 types with pros and cons), embeddings, retrieval (flat index, hierarchical, hypothetical questions, HyDE, small-to-big, contextual retrieval, adaptive retrieval, query expansion, reranking), judgment models, response quality and safety
7. Metrics and Evaluation (similarity metrics, BLEU/ROUGE, human review, tools like Langfuse, Opik, Ragas, LangSmith)
8. Databases (vector DBs, search engines, Postgres extensions, FAISS)
9. Production Considerations (checklist bullets, no links)
10. Platform-specific (Supabase guide)
11. Best Practices (checklist bullets, no links)

Quality notes from reading it:
- Strong as a map. Weak as a teacher: many entries are short bullets, Medium posts or YouTube links.
- Several lists have no links at all (Architecture Patterns, Production Considerations, Best Practices). Those are good topic checklists but not sources.
- Errors seen: the Qdrant entry links to the Neo4j repo. The "Cosine similarity" note says cosine and dot product are "generally seen as the most effective" with no source. BLEU, ROUGE and METEOR are listed for response evaluation, but they are weak fits for RAG answers (my opinion).
- Some links redirect now (LlamaIndex docs moved to developers.llamaindex.ai; the LangGraph agentic RAG page showed only "Redirecting...").
- The HyDE entry points to a blog (pixion.co), not the paper. I fetched the paper myself (see below).

## 2. Topic to resource map

Only resources I opened are marked "read". Level is my judgment.

| Topic | Resource | Plain-English description | Level |
|---|---|---|---|
| Whole pipeline, hands-on | https://github.com/NirDiamant/RAG_Techniques (read, first 100k of 126k chars) | Runnable notebooks, grouped from foundational to advanced: chunk sizes, query changes, reranking, graph, agentic, evaluation. | beginner to advanced |
| Chunking | Repo's Chunking section (read, in README) | Six chunking styles with use case, pros, cons. Gives 256-512 token size and 10-20% overlap as typical (repo claim, no source). | beginner |
| Chunking context fix | https://www.anthropic.com/engineering/contextual-retrieval (read) | Add a 50-100 token note to each chunk saying where it came from, before indexing. Top-20 miss rate went 5.7% to 3.7%; with BM25 to 2.9%; with reranking to 1.9%. | intermediate |
| Embeddings | https://huggingface.co/spaces/mteb/leaderboard (listed in repo, not opened) | Public score board to compare embedding models. | beginner |
| Embedding tuning | LlamaIndex production RAG guide, https://developers.llamaindex.ai/python/framework/optimizing/production_rag/ (read) | Fine-tune the embedding model on your own data when stock models miss your domain terms. | advanced |
| Reranking | https://developer.nvidia.com/blog/enhancing-rag-pipelines-with-re-ranking/ (read) | Fetch 45 candidates fast, let a stronger model score each against the question, keep the top 5. | intermediate |
| Reranking, cost options | LlamaIndex production RAG guide (read) | Retrieve 10-20, rerank to 3-5. Local cross-encoder is the suggested default; LLM-as-reranker costs most. | intermediate |
| Query rewriting | https://haystack.deepset.ai/cookbook/query-expansion (read) | An LLM writes about 4 similar queries; search for each; merge. Example: "climate change" search went from 3 to 6 documents. | intermediate |
| HyDE | https://arxiv.org/abs/2212.10496 (read abstract; not linked from the repo) | The model writes a fake answer first; the fake answer is used to search. Reported as strong with no labeled training data. | advanced |
| Hybrid search | Contextual Retrieval post (read) plus repo Best Practices line "combine vector and BM25" | BM25 catches exact terms such as IDs and error codes that embeddings miss. Combined beats embeddings alone. | intermediate |
| Graph RAG | https://github.com/microsoft/graphrag (read) | LLM turns text into a graph, then uses it to answer questions about private data. Warns indexing "can be an expensive operation". Repo is in maintenance mode, research code. | advanced |
| Vectorless / tree RAG | https://github.com/VectifyAI/PageIndex (read) | Builds a table-of-contents style tree; an LLM walks the tree. Claims 98.7% on FinanceBench vs 50% for vector RAG (vendor claim, not checked). | advanced |
| Agentic RAG | https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/ (redirect only, content NOT read) | Listed by repo as a retrieval agent tutorial. I could not read it. | intermediate (unverified) |
| Corrective RAG | https://arxiv.org/abs/2401.15884 (read abstract) | A small checker scores retrieved text; if bad, it searches the web or drops the useless parts. | advanced |
| Self-RAG | https://selfrag.github.io/ (read) | A trained model decides when to look things up and checks its own claims against sources. Needs special training. | advanced |
| Multimodal RAG | https://developer.nvidia.com/blog/an-easy-introduction-to-multimodal-retrieval-augmented-generation/ (read) | Three designs: shared image-text vector space, turn everything into text, or separate stores plus a reranker. Charts become tables. | intermediate |
| Evaluation | https://docs.ragas.io/en/stable/ (read home page) | Library for scoring LLM apps with LLM-driven metrics and experiments. The home page did not list the RAG metric names. | intermediate |
| Evaluation, more tools | Repo Tools list: Langfuse, Opik, LangSmith (names read, pages not opened) | Tracing and scoring platforms. | intermediate (unverified) |
| Production and ops | Repo "Production Considerations" (read) | Checklist: incremental indexing, versioning of embeddings and prompts, retries, A/B tests, access control, caching. No links. | beginner |
| Production patterns | LlamaIndex production RAG guide (read) | Five steps from easy to hard: separate search text from answer text, structured retrieval, routing by task, rerank, tune embeddings. | intermediate |
| Vector DBs | Repo Databases section (read): Chroma, Milvus, Pinecone, pgvector, Qdrant, Weaviate, FAISS, Elasticsearch, OpenSearch | Lists of options by type. No comparison written. Benchmark link (vectorview) not opened. | beginner |
| Safety | Repo "Prompt Injection Prevention" and "Guardrails" bullets (read) | Validate input, separate instructions from data, monitor outputs, rate limit. Links not opened. | beginner |

## 3. Topics our RAG track does not cover yet

Existing lessons: what-is-rag, whole picture, poc, reading docs, chunking, embeddings, retrieval (bm25/hybrid), prompt+citations, measure quality, debugging wrong answers, fast-cheap-safe, data freshness, going to production, launch checklist.

1. **Reranking: a second, smarter look**
   - Fetch many candidates fast, then let a stronger model pick the best 3-5. Show the 45-to-5 example.
   - Compare local cross-encoder, hosted API, and LLM as reranker by cost and delay.
2. **Rewriting the question (query expansion and HyDE)**
   - Why short or vague questions miss good chunks. Make 4 variants and merge results.
   - HyDE: write a fake answer, search with it. When it helps and when it adds wrong detail.
3. **Contextual chunks (fix chunks that lose their meaning)**
   - Add a short "where this came from" note to each chunk before indexing, for both vector and BM25 search.
   - Use the 5.7% to 1.9% miss-rate numbers as a worked example. Cover the cost with prompt caching.
4. **Agentic RAG: let the model decide how to search**
   - Model chooses whether to search, checks results, rewrites the question, and retries. Add a loop limit.
   - Cover CRAG and Self-RAG as ideas. Keep to the simple retry loop in code.
5. **Graph RAG and tree RAG: when plain chunks are not enough**
   - Questions about the whole collection ("what are the main themes") fail with top-k chunks. Show graph and document-tree ideas.
   - Be honest about the high indexing cost. Give a rule for when not to use it.
6. **Multimodal RAG: tables, charts, images, scans**
   - Three designs (shared space, all-to-text, separate stores plus reranker). Show a chart turned into a table.
   - Cover page-as-image retrieval as an alternative (repo lists Vision-RAG; not read).
7. **Choosing a vector database**
   - Four groups: Postgres extension, dedicated vector DB, search engine, in-memory library. Pick by size, filtering and ops effort.
   - Index types (HNSW, IVF) in plain words. The repo only names them.
8. **Metadata, filters and small-to-big retrieval**
   - Search small chunks, return bigger parents. Filter by date, owner, type before searching.
   - Ties to data freshness and access control lessons.
9. **Security: prompt injection and private data**
   - Documents can contain instructions that hijack the model. Show separation of instructions from data and access checks per user.
   - Our fast-cheap-safe lesson may cover part of this. Check before writing.
10. **Observability and feedback loops**
    - Log each question, the chunks found, the answer. Review failures weekly; turn them into test questions.
    - Tools: Langfuse, Opik, LangSmith (names only, unverified).
11. **Fine-tuning embeddings or the model (RAFT) and context compression**
    - When stock embeddings fail on your domain terms. When a long context window or a cache replaces RAG (Contextual Retrieval post says under 200,000 tokens may not need RAG).

Top gaps by value for readers: reranking, query rewriting/HyDE, contextual chunks, agentic RAG, vector DB choice. Graph and multimodal come next.

## 4. Dig deeper: reading path

1. Beginner: this repo's README sections "General Information", "Chunking", "Best Practices". Then the repo's LangChain and LlamaIndex starter tutorials (links not opened, unverified).
2. Beginner: NVIDIA reranking blog (read). Gives the two-step idea with a worked example.
3. Intermediate: Anthropic Contextual Retrieval (read). Numbers for hybrid search, reranking and cost.
4. Intermediate: Haystack query expansion cookbook (read).
5. Intermediate: LlamaIndex production RAG guide (read).
6. Intermediate: NVIDIA multimodal RAG intro (read).
7. Intermediate: NirDiamant RAG_Techniques notebooks. Pick one per topic and run it.
8. Intermediate: Ragas docs, then build a 20-question test set (read home page only).
9. Advanced: HyDE paper (arXiv 2212.10496), CRAG paper (arXiv 2401.15884), Self-RAG page.
10. Advanced: Microsoft GraphRAG and PageIndex repos. Read the cost warnings first.

## 5. What I could not verify

- Agentic RAG LangGraph tutorial: fetch returned only a redirect notice. Its contents are not confirmed.
- RAG_Techniques page: I read 100,000 of 126,120 characters. Later techniques are unread.
- Ragas: home page gave no metric list. Faithfulness, answer relevancy, context precision and recall are the names I remember, unverified.
- Not opened: MTEB leaderboard, vector DB benchmark, Langfuse, Opik, LangSmith, Pixion blog posts, IBM guardrails guide, HiddenLayer injection guide, Vision-RAG video, CAG article, FLARE, RAFT, REFRAG, VideoRAG, A-RAG, the Supabase doc, and the rest of the Python ecosystem doc beyond its first 80 lines.
- Claims quoted from vendors (PageIndex 98.7%, Self-RAG beating ChatGPT) are as stated on their pages and not independently checked.
- Chunk size and overlap numbers in the repo have no cited source.
- Whether the repo's links are all alive: I only tested those I fetched. Two redirected.
- Repo star count, last update date and contributor activity were not checked.

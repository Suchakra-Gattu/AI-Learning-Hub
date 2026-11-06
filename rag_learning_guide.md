# RAG, Deeply: A Self-Paced Curriculum (General Theory + RAGFlow Internals)

> **Important context-setting note before you start:** the RAGFlow repository you have checked out (`/home/suchakragattu/ragflow`) is a **full Go rewrite** of the original Python RAGFlow project. Everything that used to live in Python's `api/`, `rag/`, `deepdoc/`, `graphrag/` now lives under `internal/*.go`. There is no Python `rag/` or `deepdoc/` package in this checkout — only a `sdk/python` client SDK and a couple of standalone Python scripts under `tools/`. This guide cites the **real Go files** that now implement each concept, and explains their mechanisms in Python/JS terms without trying to teach you Go syntax. Every RAGFlow-specific claim below was produced by actually reading the source in this repo; where something could not be verified, that is stated explicitly rather than guessed.

---

## 0. How to use this guide

Each module below follows the same four-part shape:

1. **The general concept** — what it is and why it exists, sourced from the original paper or canonical reference.
2. **Industry technique variants** — how the concept shows up in production systems today (LangChain, LlamaIndex, Pinecone, Anthropic, Cohere, etc.), sourced from official docs.
3. **How RAGFlow does this** — real file paths in this repo, line numbers, and a plain-language explanation of the mechanism.
4. Where relevant, a comparison table.

You do not need to read this top-to-bottom in one sitting. Suggested pacing if treating this as a multi-week self-study:

| Week | Modules | Focus |
| --- | --- | --- |
| 1 | 1 (Why RAG), 2 (Parsing/Ingestion) | Get the big picture; see how messy raw documents become usable text |
| 2 | 3 (Chunking) | The single highest-leverage design decision in any RAG system |
| 3 | 4 (Embedding), 5 (Indexing/Storage) | How text becomes searchable vectors and how they're stored |
| 4 | 6 (Retrieval), 7 (Reranking) | The actual search mechanics: dense, sparse, hybrid, fusion, cross-encoders |
| 5 | 8 (Query Understanding), 9 (Generation & Citation) | Making retrieval smarter before search, and trustworthy after |
| 6 | 10 (Advanced Architectures: RAPTOR/GraphRAG/Self-RAG/CRAG/Agentic RAG) | How RAGFlow's agentic retrieval and knowledge-graph features fit the SOTA landscape |
| 7 | 11 (Evaluation) | How you'd actually know if any of this works |
| 8 | 12 (Best Practices), 13 (Gaps), 14 (References) | Production hygiene and an honest accounting of what's NOT in this repo |

Code citations use the form `path/to/file.go:123` (line 123) or `path/to/file.go:120-140` (a range). All paths are relative to the repo root unless given as absolute paths.

---

## 1. Why RAG Exists

### 1.1 The general concept

Retrieval-Augmented Generation was introduced by Lewis et al. in **"Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"** (NeurIPS 2020). The core idea: instead of relying solely on parameters memorized during pretraining, combine a parametric language model with a non-parametric memory — a dense vector index over an external corpus — that is queried at inference time, and condition generation on the retrieved passages. This grounds the model's output in retrievable evidence rather than purely in what it memorized during training. Source: [arXiv:2005.11401](https://arxiv.org/abs/2005.11401).

### 1.2 Why not just fine-tune, or just use a longer context window?

Three different tools solve three different problems:

- **Fine-tuning** changes model *behavior* (tone, format, task specialization, domain vocabulary) from labeled examples, but is not a dependable, auditable store of facts, and does not give you per-answer citations back to a verifiable source — new/changing facts require retraining.
- **Long context** lets you stuff more raw material into a single request, which works well when relevant evidence is distributed broadly across many documents and you need cross-document reasoning. But it has real costs: quadratic attention-scaling costs, "lost in the middle" degradation as context grows, persistent knowledge cutoffs, and a higher chance of irrelevant/noisy content diluting the model's attention.
- **RAG** is the right tool when the relevant evidence for any one query is a *small, sparse* subset of a much larger, frequently-changing corpus, and you need citations/provenance. It avoids re-encoding your entire knowledge base on every request.

In practice, production systems increasingly combine all three (e.g., RAG supplies candidate evidence, a long-context model reasons over more of it than classic top-5 retrieval would allow, and the base model may be lightly fine-tuned for citation style).

### 1.3 How RAGFlow does this

RAGFlow is architected purely around the RAG pattern: documents are ingested into a knowledge base once, and every chat/agent turn performs retrieval against that knowledge base before (or interleaved with) generation. There is no model fine-tuning pipeline in this repo at all — RAGFlow only calls out to externally-hosted or self-hosted chat/embedding/rerank models through a provider abstraction (see Module 4 and 9). The entire value proposition of the product is making retrieval-time grounding (ingestion, chunking, indexing, retrieval, reranking, citation) as good as possible, since it does not control or fine-tune the underlying LLM.

---

## 2. Document Parsing / Ingestion

### 2.1 The general concept

Before anything can be embedded or indexed, raw files (PDF, Word, slides, spreadsheets, scanned images, web pages) must be turned into clean, structured text. This step is frequently the dominant source of RAG quality problems in practice — garbled OCR, lost table structure, or wrong reading order silently corrupts everything downstream. Production parsing pipelines generally need: file-type detection, text extraction, OCR for scanned/image content, layout analysis (what region is a title vs. body vs. table vs. figure), and table-structure reconstruction.

### 2.2 Industry technique variants

- **Text-layer extraction** for digital-native PDFs/Office docs (e.g., `pdfplumber`, `PyPDF2`, `python-docx`, `openpyxl` in the Python ecosystem).
- **OCR** for scanned/image-based content, typically a two-stage pipeline: a **text detector** (locate bounding boxes of text regions, e.g., the DB/Differentiable-Binarization detector used by PaddleOCR) followed by a **text recognizer** (CTC-based sequence decoding of each cropped box).
- **Document Layout Analysis (DLA)**, typically an object-detection model (YOLO family or a dedicated layout model) that classifies page regions as title/text/table/figure/caption, used to establish reading order and section structure.
- **Table Structure Recognition (TSR)**, a secondary detector that identifies row/column/cell boundaries within a region already classified as a table, then reconstructs it as structured HTML/CSV.
- **Cloud document-AI APIs** (AWS Textract, Google Document AI, Azure Document Intelligence) as an alternative to self-hosted models.

### 2.3 How RAGFlow does this

**File-type dispatch.** `internal/utility/file.go:32-50,74` (`GetFileType`) is a simple extension → type lookup (think a Python `dict` keyed by lowercased file extension) producing one of: `pdf, doc, docx, ppt, pptx, xls, xlsx, csv, html, md, txt, epub, json, video, email, visual, aural, folder, other`. The actual parser-construction factory — a dispatcher, like a Python `if/elif` chain or a registry `dict` of constructor functions — is `GetParser` at `internal/parser/parser/parser_type.go:31-68`, which builds the right parser struct per file type (PPTX/PPT, XLSX/XLS, CSV, DOCX/DOC, PDF, HTML, Markdown, plain text/code, EPUB, JSON/JSONL, Email, Picture \[vision-model-based\], Audio). This is wired into the overall ingestion pipeline by `dispatchParse` in `internal/ingestion/component/parser_dispatch.go:80-115`.

**PDF parsing — the deepest pipeline, with selectable backends.** `internal/parser/parser/pdf_parser_common.go:46-56` lists selectable PDF parse methods: `deepdoc` (default, fully local/offline), `plain_text` (just the embedded text layer, no vision at all), and five remote/cloud engines (`mineru`, `paddleocr`, `docling`, `opendataloader`, `somark`, `tcadp`) that simply POST file bytes to an externally configured HTTP service and poll for structured JSON back — no local ML for those.

The **default local "deepdoc" pipeline** (`internal/deepdoc/native/` + `internal/deepdoc/parser/pdf/`) is a line-by-line Go port of the original Python RAGFlow's `deepdoc/vision` module (confirmed by doc-comments in the Go source citing the Python files directly), and is genuinely the most technically interesting part of the ingestion stack:

- **PDF engine split**: text/character/table extraction uses a Rust-via-cgo library called `pdf_oxide` (`internal/deepdoc/parser/pdf/parse_cgo.go:27`), while page-to-bitmap **rasterization** (needed so vision models can see the page) uses Google's **libpdfium** bound via raw cgo (`internal/deepdoc/parser/pdf/pdfium/pdfium.go:1-10`) — analogous to the Python stack using `pdfplumber`/`PyPDF` for text plus `pypdfium2` for rendering.
- **Per-page decision logic** (`internal/deepdoc/parser/pdf/parser.go:169-272`, `processPage`): extract embedded characters, render the page as a bitmap, then decide whether the page needs full OCR (if the embedded text layer is empty/garbled, or the page is visually "scan noise") versus just merging embedded characters directly into text boxes with OCR used only for gaps. Pages with no detectable text are retried at up to 9x zoom to catch tiny scanned text.
- **OCR text detection** (`internal/deepdoc/native/det.go`) is a Go port of **PaddleOCR's DB (Differentiable Binarization) detector**: runs an ONNX model (`det.ort`, via `github.com/infiniflow/onnxruntime_go`, confirmed at `internal/deepdoc/native/ocr_rec.go:21`) and does the post-processing (binary segmentation, contour-following, min-area-rectangle fitting, box "unclip" expansion) natively in Go, with dedicated parity tests asserting the output matches the Python reference to within \~1e-3–1e-4.
- **OCR text recognition** (`internal/deepdoc/native/ocr_rec.go:1-30`) is a port of **PP-OCRv4's CTC recognizer**: resizes each detected text-line crop to 48×320, runs a `rec.ort` ONNX model, and CTC-decodes against a 6625-entry character dictionary (Chinese + English + punctuation).
- **Layout detection / DLA** (`internal/deepdoc/native/dla.go:1-56`) ports `LayoutRecognizer4YOLOv10` — a **YOLOv10** object detector (`layout.ort`) run over a 1024×1024 letterboxed page, classifying regions into title / text / reference / figure / figure caption / table / table caption / equation. This region map drives reading order and the chunking of titled sections (see Module 3).
- **Table Structure Recognition (TSR)** (`internal/deepdoc/native/tsr.go:1-26`): for every DLA-tagged table region, crops it and runs a `tsr.ort` model detecting table/column/row/column-header/projected-row-header/spanning-cell classes; results are assembled into a grid and serialized as real HTML `<table>` markup (`internal/deepdoc/parser/pdf/table/table_html.go`), i.e. scanned tables are reconstructed as structured tables, not dumped as loose text.
- All four ONNX models run CPU-only through a shared inference wrapper (`internal/deepdoc/native/session.go`) with a process-wide concurrency limiter — fully local/offline for the default path, no GPU and no external API call.
- Higher-level cleanup — multi-column detection, de-hyphenation across line wraps, table-of-contents/header/footer removal — lives in `internal/deepdoc/parser/pdf/layout/` and is toggled via `PDFParser` flags (`RemoveTOC`, `RemoveHeaderFooter`, `EnableMultiColumn`, `internal/parser/parser/pdf_parser_common.go:69-71`).

**Office formats.** DOCX and PPTX/PPT go through a native Rust-via-cgo library, `office_oxide` (only entry point: `internal/deepdoc/parser/office/engine_cgo.go:40-61`), which extracts a structured intermediate representation, Markdown, and plain text in parallel. A non-cgo build variant hard-fails (`engine_nocgo.go`) — there is no pure-Go DOCX/PPTX fallback. `internal/deepdoc/parser/office/office_detect.go:17-27` magic-byte-sniffs the container format (OOXML zip vs. legacy OLE binary) so a mislabeled extension still opens correctly. **XLSX** uses the pure-Go `excelize` library (Go's rough equivalent of `openpyxl`); **XLS** (legacy binary) uses a separate pure-Go reader. All three office parsers also carry optional fields to route through the same remote "TCADP" cloud-reconstruction backend used for PDFs.

**Web pages.** There is **no crawler inside the knowledge-base ingestion pipeline itself** — an uploaded `.html` file is parsed like any other file via the HTML parser. Web crawling exists only in two unrelated places: (1) `internal/agent/tool/crawler.go:34-50`, a single-page-fetch tool an **agent/canvas workflow** can call at chat time, not at ingestion time; and (2) `tools/firecrawl/`, a standalone Python script wrapping the Firecrawl API, which lives outside the Go ingestion tree entirely and is not wired into the knowledge-base pipeline.

**The end-to-end ingestion task lifecycle.** Status is a state machine (`internal/common/constants.go:32-64`): `CREATED → SCHEDULED → RUNNING → {COMPLETED | FAILED | STOPPED}`. Tasks are lightweight wake-up messages published to a NATS JetStream subject (`internal/common/task.go:24,41-44`) — think of NATS here the way you'd think of Celery/RQ backed by Redis/RabbitMQ, just with a different broker. `IngestionTaskService.CreateForDocuments` (`internal/service/ingestion_task_service.go:65-146`) is the producer. On the consumer side, a pool of worker goroutines (a goroutine is a lightweight cooperatively-scheduled thread — think a Python `asyncio` task or a thread-pool worker) pulls messages and runs each task through `PipelineExecutor.Execute` (`internal/ingestion/task/pipeline_executor.go:207-253`). Notably, **the ingestion pipeline itself is modeled as a DAG/flowchart** ("canvas") — the same abstraction RAGFlow uses for chat agent workflows (see Module 10): a JSON graph of `File → Parser → Chunker → Extractor → Tokenizer` nodes (`internal/ingestion/pipeline/pipeline.go:100-123`). The embedding call happens inside the `Tokenizer` node (Module 4); the final indexing write happens in `internal/ingestion/task/chunk_index_writer.go:33-46`, batching chunk+vector+metadata records into the configured search engine with retries. Live progress is reported back to the UI via a `ProgressSink` interface (`internal/ingestion/pipeline/pipeline.go:79-95`), with a specific hook (`attachPDFPageProgress`, `internal/ingestion/component/parser_dispatch.go:143-154`) wiring per-page OCR completion into that percentage.

---

## 3. Chunking Strategies

### 3.1 The general concept

Chunking is the decision of how to split a document into retrievable units. It is arguably the single highest-leverage lever in a RAG system: chunks too large dilute relevance and waste context budget; chunks too small lose necessary surrounding context. Every chunking strategy is a tradeoff between **semantic coherence** (does a chunk represent one complete idea?) and **retrieval precision** (is each chunk focused enough that embedding similarity actually isolates the relevant part?).

### 3.2 Industry technique variants

| Strategy | What it does | Source |
| --- | --- | --- |
| Fixed-size | Split into N-token windows, usually with overlap | [Pinecone: Chunking Strategies for LLM Applications](https://www.pinecone.io/learn/chunking-strategies/) |
| Recursive character splitting | Try a sequence of separators (`\n\n`, `\n`, sentence, word) in priority order until chunks fit the size budget | Pinecone, above; LangChain `RecursiveCharacterTextSplitter` |
| Semantic chunking | Embed consecutive sentences, split where cosine distance between neighbors crosses a threshold (topic shift detection) | Pinecone, above |
| Sentence-window | Index single sentences, but retrieve with a window of N neighboring sentences for added context at generation time | [LlamaIndex: SentenceWindowNodeParser](https://developers.llamaindex.ai/python/framework-api-reference/node_parsers/sentence_window/) |
| Hierarchical / parent-document | Split into small child chunks for precise retrieval, but return the containing larger parent chunk as the actual context given to the LLM | [LlamaIndex: Hierarchical node parser](https://developers.llamaindex.ai/python/framework-api-reference/node_parsers/hierarchical/) |
| Late chunking | Run the full document through a long-context embedding model's transformer layers first, THEN pool token vectors per chunk — so each chunk embedding is conditioned on the whole document's context, instead of chunk-then-embed | [Jina AI: Late Chunking in Long-Context Embedding Models](https://jina.ai/news/late-chunking-in-long-context-embedding-models/) |

### 3.3 How RAGFlow does this

Every classic RAGFlow (Python-era) "parser mode" — `naive`, `qa`, `manual`, `table`, `paper`, `book`, `laws`, `presentation`, `picture`, `one`, `audio`, `email` — now exists as a **built-in ingestion-pipeline template**: a pre-made canvas DSL JSON file embedded in the binary at `internal/ingestion/pipeline/template/ingestion_pipeline_<name>.json`, registered by `internal/ingestion/pipeline/builtin_registry.go:19-33,139-142`. (`"naive"` is kept only as a legacy alias for `"general"` — it is not a separate behavior.) **`resume` (CV parsing) mode was not found anywhere in the Go code** — it appears to have been dropped in this rewrite. `knowledge_graph` and `tag` still exist, but relocated to cross-cutting post-chunking pipeline stages rather than chunk-splitting modes (see below and Module 10).

| Mode (template) | Chunker component | Mechanism |
| --- | --- | --- |
| **general** (`ingestion_pipeline_general.json`) | `GeneralChunker` (`internal/ingestion/component/chunker/general.go:176-199`) | Format-specific strategy per file type; ultimately splits on a configurable delimiter list and greedily merges pieces up to a token budget (`chunk_token_size`, default 512) with optional overlap. This is the renamed "naive" default. |
| **qa** | `QAChunker` (`internal/ingestion/component/chunker/qa.go:17-29`) | Extracts question/answer pairs instead of prose spans — delimiter-separated rows for text/CSV, heading-based pairs for Markdown, first-two-columns for tables. One chunk = one Q&A pair, formatted `"Question: {q}\tAnswer: {a}"`. |
| **manual** | `ManualChunker` (`internal/ingestion/component/chunker/manual.go:17-37`) | Like heading-grouping, but first re-sorts text records into true `(page, top, left)` reading order — needed because multi-column manuals emit text column-by-column, which would otherwise interleave left/right content. |
| **table** | `TableChunker` (`internal/ingestion/component/chunker/table.go:17-27`) | One table row = one chunk, rendered as `"- field: value"` lines. |
| **paper** | `TitleChunker`, method=`group`, hierarchy=0 | Groups adjacent text under the same shallow heading into merged chunks up to a token budget. |
| **book** | `TitleChunker`, method=`hierarchy`, hierarchy=5, `include_heading_content=true` | Builds a 5-level heading tree, walks it depth-first; each chunk includes the text of all ancestor headings so a deeply nested section remains self-describing. |
| **laws** | `TitleChunker`, method=`hierarchy`, hierarchy=2, `include_heading_content=false` | Same hierarchy algorithm as "book" but shallower (e.g. 章/条 — chapter/article), without repeating ancestor heading text. |
| **presentation** | `PageChunker` (`internal/ingestion/component/chunker/page.go:17-28`) | One slide/page = one chunk, unchanged. |
| **picture / audio / one** | `OneChunker` (`internal/ingestion/component/chunker/one.go:17-26`) | The entire document (or image/audio file) becomes exactly one chunk. |
| **email** | `TokenChunker`, delimiter mode | General token-budget splitting applied to email body/headers. |

Heading detection for the `TitleChunker` family (`internal/ingestion/component/chunker/title.go:17-55`) is layered: (1) native PDF outline/bookmark metadata when present, (2) user-configurable regex per heading level (e.g. Markdown `^#`/`^##`, or Chinese legal numbering `第...章`/`第...条`), (3) DLA layout-hint fallback (title/section regions from Module 2's layout model), (4) a generic bulleted/numbered-list regex as last resort.

**Chunk size / overlap** are schema fields on `internal/ingestion/component/schema/chunker.go:186-199` (`chunk_token_size` default 512, `overlapped_percent` default 0, normalized range \[0,90\]), baked as defaults into each builtin template but editable per-dataset — `internal/ingestion/pipeline/component_params.go:13-73` exposes every component's params to the frontend, and a dataset's `parser_config` API field overrides the chunker node's params at run time.

**Parent/child chunking** (hierarchical / small-to-big retrieval, same spirit as LlamaIndex's `ParentDocumentRetriever`): `GeneralChunker`/`TokenChunker` support a `children_delimiters` param — when set, each parent chunk is further split into finer child chunks, linked together, and materialized into actual parent/child index records by `indexdoc.MaterializeParentChunks` (`internal/ingestion/task/pipeline_executor.go:294`).

**Semantic (embedding-similarity) chunk *splitting* was not found.** No chunker in this repo decides split points by comparing adjacent-sentence embedding similarity the way Pinecone's semantic-chunking recipe does. The closest related feature, **RAPTOR** (`internal/ingestion/component/knowledge_compiler/tree/raptor.go`), clusters already-produced chunk embeddings and has an LLM summarize each cluster recursively — this augments the index with a tree of summary nodes *after* chunking, rather than changing where the original text gets split. See Module 10 for the full RAPTOR/knowledge-graph discussion.

---

## 4. Embedding

### 4.1 The general concept

An embedding model maps text into a fixed-dimensional vector such that semantically similar text ends up nearby in vector space (typically measured by cosine similarity). RAG systems embed each chunk once at ingestion time and embed the user's query at search time, then use vector similarity as (part of) the relevance signal.

### 4.2 Industry technique variants

Modern embedding models are usually **asymmetric** for retrieval: the same model family exposes a "document"/"passage" encoding mode and a separate "query" encoding mode, because queries and passages have different statistical structure (short questions vs. longer prose) — providers like Cohere (`search_query` vs `search_document`), Voyage AI (`query` vs `document`), and Jina (`retrieval.query` vs `retrieval.passage`) all implement this distinction explicitly in their APIs. Batching, token-limit truncation, and request-level caching are standard production concerns since embedding is billed per token and rate-limited per provider.

### 4.3 How RAGFlow does this

**Provider abstraction.** `internal/entity/models/types.go:43-76` defines `ModelDriver`, a Go `interface` — think a Python `Protocol`/abstract base class: any struct implementing its methods satisfies it without an explicit "implements" declaration. The relevant method is `Embed(ctx, modelName, request, apiConfig, embeddingConfig, modelUsage) ([]EmbeddingData, error)`. Over 70 provider files in `internal/entity/models/` (`openai.go`, `cohere.go`, `jina.go`, `voyage.go`, `huggingface.go`, `ollama.go`, `xinference.go`, `bedrock.go`, `mistral.go`, `google.go`, etc.) each implement this method against their own HTTP request shape; `internal/entity/models/builtin.go:16-174` is a special driver that talks to a local **TEI** (Text Embeddings Inference) server for self-hosted models like BGE.

**Model catalog.** `conf/models/*.json` (\~90 provider files) declare, per vendor, which models exist and their `max_tokens`/`max_batch_size` (e.g. OpenAI `text-embedding-3-large` at 8191 tokens/2048 batch; Cohere `embed-v4.0`; Voyage `voyage-3-large`; Jina `jina-embeddings-v3/v4/v5` up to 32768 tokens). Local-runtime providers (Ollama, Xinference, HuggingFace, LM Studio, vLLM) have no fixed catalog — the user supplies a free-form model name and the driver forwards it as-is.

**Where embedding actually happens at ingestion.** `internal/ingestion/component/tokenizer.go`'s `TokenizerComponent.Invoke` (line 343) calls `embedChunks` (lines 428-607), which: builds the text-to-embed per chunk, checks a **per-chunk cache** (see below), batches cache-misses by `embedder.BatchSize()` (default 16, resolved per-model from the provider catalog), and calls `embedder.Encode(ctx, texts)` per batch (`internal/ingestion/task/embedder.go:125-176`). That function wraps the raw provider call with token-limit trimming, a shrink-and-retry "ladder" on over-limit rejections (lines 140-176), and a final per-input isolation fallback (lines 352-383) so one pathological chunk can't fail an entire document's ingestion. A separate title-text vector is also computed and blended with the content vector via weighted averaging (`tokenizer.go:521-538,637+`) — the "filename embedding weight" feature from the original Python RAGFlow. The resulting vector is stored on the chunk under a dimension-encoded field name, `q_<dims>_vec` (`tokenizer.go:588`) — the same naming convention the storage engines rely on (Module 5).

**Caching.** A per-chunk embedding cache keyed on `("emb", embd_id, chunk_id, trimmed_text)` is backed by **kvrocks** (a Redis-protocol-compatible KV store), with a 7-day TTL as a backstop (`internal/ingestion/chunkcache/chunkcache.go:46`) — purged immediately once a task's chunks are durably indexed. This exists specifically so a crashed/retried ingestion task doesn't re-pay for embeddings it already computed.

**Concurrency and rate-limit coordination.** Embedding batches within a single document run sequentially (no goroutine fan-out per document), but multiple documents/tasks run concurrently across a worker pool. Critically, `internal/ingestion/task/embedder.go:411-476` implements a **shared rate-limit cooldown**, keyed by provider+credentials+model, so that when one worker hits a provider's 429, *every* worker sharing that quota backs off together instead of independently hammering an exhausted token-per-minute budget.

**Query-time embedding differs from ingestion-time.** `internal/service/nlp/retrieval.go:993-1020`'s `GetVector` calls `embModel.Embed(ctx, EmbedRequest{Texts: []string{txt}, Query: true}, ...)` — single text, no batching, no cache, no retry ladder. The `Query: true` flag is what selects a provider's asymmetric query-mode encoding (Cohere/Voyage/Jina as described in 4.2) — this is load-bearing: if you skip it, the query vector lands in the wrong part of the embedding space for providers that distinguish query vs. document encoding.

---

## 5. Indexing / Storage

### 5.1 The general concept

A production RAG index needs to store, per chunk: the text, a dense vector, and structured metadata (source document, position, tags, dates) — and support efficient approximate nearest-neighbor (ANN) search over the vectors (commonly HNSW graphs) alongside full-text/BM25 search, ideally in one combined query.

### 5.2 Industry technique variants

Common production choices: dedicated vector databases (Pinecone, Weaviate, Qdrant, Milvus), vector-search-capable general search engines (Elasticsearch/OpenSearch `dense_vector` + `knn`), or Postgres with `pgvector`. HNSW (Hierarchical Navigable Small World graphs) is the dominant ANN index type, tuned via parameters like `M` (graph connectivity) and `ef_construction`/`ef_search` (build/search breadth).

### 5.3 How RAGFlow does this

**The abstraction.** `internal/engine/engine.go:42-101` defines `DocEngine`, a large interface (\~25 methods: chunk CRUD, search, metadata CRUD, generic document indexing, result-processing helpers, raw SQL, lifecycle) — think an abstract base class that every pluggable backend must fully implement. `internal/engine/global.go` is a singleton factory: based on config, it constructs exactly one of **elasticsearch, infinity, oceanbase (shared with "seekdb"), serenedb, or vastbase** as the concrete `DocEngine`. A second interface, `MessageQueue` (`engine.go:128-155`), is implemented only by **nats** (the async task-distribution broker). **kvrocks** is not a `DocEngine` at all — it's a Redis-protocol KV store used for caching and ID generation. **clickhouse** is a thin, mostly-stubbed usage-stats hook gated behind an enterprise-edition build flag, effectively inert in the OSS build.

**Elasticsearch schema (the best-documented backend).** `internal/engine/elasticsearch/client.go:85` applies a global index template (`conf/mapping.json`) with **naming-convention-driven dynamic field mapping** — carried over verbatim from the Python original: fields ending `_kwd`/`_id`/`_uid` → `keyword`; `_tks` → `text` with a custom scripted-BM25-like similarity and whitespace analyzer (RAGFlow pre-tokenizes itself); `_int`/`_long`/`_flt` → numeric; `_dt`/`_at` → `date`; `_fea`/`_feas` → `rank_feature`/`rank_features` (used for PageRank and tag-boost scores); and critically **`q_*_vec` → `dense_vector`, `index: true`, `similarity: cosine`** (`conf/mapping.json:160-169`). No explicit HNSW tuning is set for Elasticsearch — ES 8's defaults apply, and dimensionality is inferred from the field name itself (e.g. `q_1024_vec`), which is how a knowledge base can switch embedding models without a migration: old chunks keep their old `q_768_vec` field, new chunks get a new `q_1024_vec` field, and search just targets whichever field matches the configured model. Insertion (`internal/engine/elasticsearch/chunk.go:181-321`) writes **one Elasticsearch document per chunk**, using the chunk's own ID as the ES `_id`, batched ≤500 chunks/≤20MB per bulk call. The concrete per-chunk field set is defined in `internal/ingestion/component/schema/chunk_types.go:106-140`: `content_with_weight`, `title_tks`/`content_ltks` (tokenized text for BM25), `doc_type_kwd`, `chunk_order_int`, `page_number`, `positions`, `questions`, `keywords`, `summary`, plus a dynamic extra bag for images/layout/table data; `doc_id`/`kb_id` are stamped on at insert time.

**Infinity (RAGFlow's own engine) differs structurally** — it's a strongly-typed table engine, not dynamically mapped. The static schema (`conf/infinity_mapping.json`) declares explicit typed columns; the **vector column is added programmatically**, not statically — `internal/engine/infinity/chunk.go:92-230` does `CreateTable` with an appended `q_<dims>_vec` column on first use, or `ALTER TABLE ADD COLUMN` for a newly-seen dimensionality (same "one column per embedding size" trick as Elasticsearch, just via explicit DDL). Infinity is also the **only engine in this repo where RAGFlow itself configures HNSW tuning parameters explicitly**: `M=16`, `ef_construction=50`, `metric=cosine`, plus `encode=lvq` (locally-adaptive vector quantization, a compression scheme) (`internal/engine/infinity/chunk.go:212-228`).

**Raw file storage.** Original uploaded files (PDFs, DOCX, images) go to a separate object-storage layer — `internal/storage/types.go:59-110` defines a `Storage` interface (`Put`/`Get`/`Remove`/presigned URLs/bucket ops) implemented by MinIO, AWS S3, Alibaba OSS, and Google Cloud Storage backends, selected via the same singleton-factory pattern (`internal/storage/storage_factory.go`). This is a clean separation: raw bytes live in object storage, parsed/chunked/embedded *content* lives in the `DocEngine`.

---

## 6. Retrieval / Search Harness

### 6.1 The general concept

Retrieval has two classic families: **sparse/lexical** search (BM25 — exact term overlap, fast, interpretable, good at rare/specific terms and IDs) and **dense/semantic** search (embedding cosine similarity — good at paraphrase and conceptual matches, weak at exact identifiers). **Hybrid search** combines both, typically via either a weighted linear combination of normalized scores, or **Reciprocal Rank Fusion (RRF)** — introduced by Cormack, Clarke & Buettcher (SIGIR 2009), which combines ranked lists by summing `1/(k + rank)` across lists for each document, avoiding the need to calibrate incompatible score scales.

### 6.2 Industry technique variants

- Pure dense (vector-only) retrieval — simplest, but fails on exact-match/rare-term queries.
- Pure sparse (BM25) — strong on precision for exact terms, weak on paraphrase/synonymy.
- **Hybrid with RRF** — the most common production pattern precisely because it sidesteps score-scale mismatches between BM25 and cosine similarity.
- **Metadata filtering** — scoping search by structured fields (tags, dates, source) before or alongside vector/lexical scoring.
- **Agentic/iterative retrieval** — instead of one retrieve-then-generate pass, an LLM-driven loop repeatedly chooses which retrieval tool to call and reads results before answering (see Module 10).
- **Knowledge-graph retrieval** — traversing an entity/relationship graph to answer multi-hop/relational questions that a single passage can't answer alone (see Module 10).

### 6.3 How RAGFlow does this

**Three retrieval modes, selected per request.** `internal/service/nlp/retrieval.go`'s `RetrievalService.Search`/`.Retrieval` (lines 97-984): no embedding model configured → pure keyword (line 769-779); `VectorOnly=true` → pure dense, explicitly bypassing any BM25 clause (line 816); otherwise → hybrid (line 818).

**Fusion is a weighted linear sum, not RRF.** This is explicit and documented in-code (`internal/service/nlp/reranker.go:406`): `sim = tkweight * tksim + vtweight * vtsim`. The same formula recurs in `RerankByModel` (reranker.go:198), `HybridSimilarity` (reranker.go:409), and `RerankWithKNN` (reranker.go:1016). At the engine-query level, Infinity gets an explicit `FusionExpr{Method: "weighted_sum", weights: "<termWeight>,<vectorWeight>"}` (`retrieval.go:620-634`); for Elasticsearch/OceanBase/Vastbase, the engine-level query hard-codes a near-degenerate weight pair (`"0.001,1"`, line 658) so the engine's own fused query is effectively a vector-ranked recall pass, and the *real* configured weight is applied afterward in a Go-side rerank step (`RerankWithKNN`) rather than inside the engine's native fusion. **No Reciprocal Rank Fusion implementation exists anywhere in this Go codebase** — all combination logic found is linear weighted sum. The default split is `vector_similarity_weight = 0.3` (70% keyword / 30% vector) for hybrid queries (`retrieval.go:121`), validated/normalized (sum to 1.0) by `internal/service/similarity_weight.go`. An additional additive term boosts scores by tag-similarity and PageRank (`applyRankFeatureScores*`, reranker.go:662-876: `sim[i] += tagScore[i]*10 + pagerank[i]`) — a hand-tuned score boost, not a rank-fusion algorithm.

**Metadata filters.** `internal/service/metadata_filter.go` supports three modes: `auto` (LLM generates filter conditions from the question), `semi_auto` (LLM restricted to a caller-chosen key subset), `manual` (caller-supplied conditions) — operators include `=, !=, >, <, in, contains, start with, empty`, etc. (`metadata_filter.go:270-505`). Filters are pushed down to the search engine when possible (`FilterDocIdsByMetaPushdown`) and fall back to in-memory filtering otherwise (`metadata_filter.go:603-627`). Standard baked-in filterable fields include `kb_id`, `doc_id`, `knowledge_graph_kwd`, `available_int`, `entity_kwd` (`retrieval.go:1023-1043`).

**Agentic retrieval — a full ReAct tool-calling loop.** This is RAGFlow's most distinctive retrieval feature. Built on the `eino` ADK framework in `internal/agentic_rag/agent.go` (`Run()`, lines 308-526): instead of "embed → top-k → generate," the LLM is handed a toolbox and repeatedly decides which tool to call, reads results, and decides again — conceptually identical to a Python agent loop (`while not done: response = llm.chat(messages, tools=tools); ...`). Tools include `grep_chunks` (regex search over content), `search_bm25_chunks`, `search_semantic_chunks` (pure vector), `search_chunks` (hybrid, agent-adjustable weight, default 0.7), `list_chunks` (fetch full original text of specific chunk IDs — the mandatory "deep read" step), `search_metadata`, `think`, `run_javascript`, plus conditionally-available `navigate_tree`/`navigate_structure`/`graph_explore` and `web_search`. The loop runs up to `MaxIterations=120` model turns (`agent.go:123`), executing same-round tool calls in parallel, ending when the model emits a tool-call-free answer; a deterministic fallback synthesis step (`finalizeAnswer`, lines 752-794) guarantees the user always gets an answer even on iteration exhaustion or error. An `EvidenceRegistry` (`internal/agentic_rag/evidence_registry.go`) stamps every passage shown to the model with a stable `[ID:n]` handle on first exposure — the model is instructed to cite only passages it was actually shown, a deliberate anti-hallucination mechanism (see Module 9). A separate, simpler mode — `internal/service/deep_researcher.go`'s `DeepResearcher` — does recursive query decomposition (retrieve → LLM sufficiency check → generate 2-3 complementary sub-queries if insufficient → recurse, max depth 3) rather than full tool-calling; it is triggered by a `reasoning=true` chat flag distinct from the `smart-reasoning` agentic mode.

**Knowledge-graph retrieval** exists as a dedicated `graph_explore` tool and a separate always-on graph-search pipeline; see Module 10 for full detail (it's covered there alongside RAPTOR and GraphRAG for direct comparison to the industry techniques).

---

## 7. Reranking

### 7.1 The general concept

A **cross-encoder** reranker jointly encodes a (query, document) pair in a single forward pass (as opposed to a bi-encoder/embedding model, which encodes query and document independently and compares vectors afterward). Because the cross-encoder can attend across both texts simultaneously, it produces a far more calibrated relevance score — at the cost of being too slow to run over an entire corpus, so it's used only to re-score a small candidate set already surfaced by cheaper first-stage retrieval.

### 7.2 Industry technique variants

Production rerankers are typically offered as a hosted API taking `(query, [documents])` and returning a reordered list with relevance scores — e.g., Cohere's Rerank models, which process query and document as a unified input in one forward pass and return a `V2RerankResponse` with per-document relevance scores on a comparable scale. Other prominent providers: Jina Reranker, Voyage Rerank, NVIDIA NemoRetriever rerankers, and open-weight BGE-reranker / Qwen3-Reranker cross-encoders.

### 7.3 How RAGFlow does this

RAGFlow supports a genuine cross-encoder reranking step, but it is architecturally folded **into** the fusion formula rather than being a wholly separate post-fusion pass. `scoreSearchResult` (`internal/service/nlp/retrieval.go:460-592`) checks whether `req.RerankModel` is set; if so, everything routes through `RerankByModel` (`internal/service/nlp/reranker.go:92-207`) *instead of* the formula-only paths. Concretely: the engine returns the top `rerankCandidatesCount` (default 64, `retrieval.go:138`) candidates from whatever first-pass search was run, and if a rerank model is configured, `RerankByModel` **replaces the vector-similarity term** of the existing weighted-sum score with the cross-encoder's score: `sim[i] = tkWeight*tsim[i] + vtWeight*modelSim[i]` (reranker.go:198) — the model is fed natural, un-tokenized chunk text (`extractNaturalText`) rather than RAGFlow's internally stemmed tokens, specifically to avoid degrading neural reranker accuracy. Because providers disagree wildly on score scale (calibrated \[0,1\] vs. raw unbounded logits), `NormalizeRerankScores` (reranker.go:227-269) min-max-rescales scores onto \[0,1\] before blending — documented in-code as necessary because, e.g., NVIDIA returns raw negative logits that would otherwise sink relevant chunks once weighted by `vtWeight=0.7`. Pagination beyond page 1 is explicitly disallowed when reranking is active (`retrieval.go:146-148`), since a single top-k rerank pass has no stable meaning beyond the first page.

**Supported reranker providers** (from `conf/models/*.json` and `internal/entity/models/*.go`, each implementing a `Rerank(...)` method): Cohere (`rerank-v4.0-pro/fast`, `rerank-v3.5`), Jina (`jina-reranker-v3`, `jina-colbert-v2`), Voyage (`rerank-2.5`), NVIDIA (`nemoretriever-rerank-v2`), and BGE-reranker / Qwen3-Reranker through many OpenAI-compatible aggregator providers (SiliconFlow, Novita, PPIO, HuaweiCloud, etc.).

A **fallback heuristic reranker** (`RerankStandard`, reranker.go:273-346) applies when no model is configured — not a learned model, just hand-rolled token-overlap scoring (content + title×2 + important-keywords×5 + question-tokens×6) combined with cosine similarity via the same weighted-sum formula.

---

## 8. Query Understanding

### 8.1 The general concept

Raw user questions are often poor search queries: they may be elliptical (relying on prior conversation turns), phrased very differently from how the answer is written (the vocabulary mismatch problem), or too narrow/too broad. Query understanding techniques transform the query before it hits the retriever.

### 8.2 Industry technique variants

- **Conversation-aware rewriting** — using chat history to produce a self-contained question (LangChain's `create_history_aware_retriever` pattern).
- **Query expansion** — adding extracted keywords/synonyms to broaden lexical recall.
- **Multi-query generation** — asking an LLM to generate several differently-phrased queries and merging results.
- **HyDE (Hypothetical Document Embeddings)** — Gao, Ma, Lin & Callan, ACL 2023 ([arXiv:2212.10496](https://arxiv.org/abs/2212.10496)): instead of embedding the raw question, prompt an LLM to generate a *hypothetical* answer document first, then embed that hypothetical document and use it for retrieval — the generated text, even if factually wrong, captures relevance *patterns* closer to how the true answer passage is written.
- **Anthropic's Contextual Retrieval** ([Anthropic Engineering, Sept 2024](https://www.anthropic.com/engineering/contextual-retrieval)): before embedding or BM25-indexing a chunk, use an LLM to generate 50-100 tokens of document-level context and prepend it to the chunk, for both the embedding index and the BM25 index ("Contextual Embeddings" + "Contextual BM25"). Reported to reduce failed retrievals by 49%, and by 67% when combined with reranking.

### 8.3 How RAGFlow does this

**Query understanding pipeline order** (`internal/service/chat_pipeline.go:174-176,609-669`), all LLM-driven and individually config-gated: `refine_multiturn` → `cross_languages` → `meta_data_filter` → keyword extraction.

- **Conversation-aware rewriting** exists (`FullQuestion`, `internal/service/generator.go:296+`): gated by `refine_multiturn` and only triggered with more than one question in the conversation — it condenses the transcript into one self-contained question, replacing implicit pronouns/references, the same pattern as LangChain's history-aware retriever. If disabled, the last user message is used verbatim.
- **Query expansion (not multi-query generation)** exists via `KeywordExtraction` (`generator.go:55`, using `internal/rag/prompts/keyword_prompt.md`): extracts top-N keywords and appends them to the retrieval text to boost lexical recall — this *adds* terms, it does not generate alternate full queries.
- **Cross-language query translation** exists (`CrossLanguages()`, `generator.go:119`, prompts in `internal/rag/prompts/cross_languages_{sys,user}_prompt.md`): translates the question into configured target languages and **replaces** the retrieval query with the translation, when enabled — single-direction translation to broaden cross-lingual recall, not simultaneous parallel multi-language retrieval.
- **Metadata-filter generation** (Module 6) is itself a form of query understanding: an LLM prompt (`internal/rag/prompts/meta_filter.md`) turns free text into structured `{conditions, logic}` JSON.
- **HyDE was explicitly NOT found.** A repo-wide search for "hyde"/"hypothetical" turned up no retrieval-related matches. Query vectors are always computed directly from the (possibly keyword-augmented/translated) user question via `GetVector` (`retrieval.go:994-1020`) — never from an LLM-generated hypothetical answer.
- **Multi-query generation exists, but only inside `DeepResearcher`** (Module 6), not the standard pipeline: `multiQueriesGenTemplate` (`internal/service/deep_researcher.go:68-107`) asks the LLM for 2-3 complementary sub-queries targeting identified information gaps, triggered only by `reasoning=true`.
- **Anthropic-style Contextual Retrieval (LLM-generated chunk-level context prepended before embedding/indexing) was not found** anywhere in the ingestion pipeline — chunks are embedded and tokenized as extracted, without an LLM-authored contextualizing preamble. This is a notable absence relative to current best practice (see Module 13).
- A related but distinct feature, `internal/service/related_question.go`, generates *post-answer* "you might also ask" suggestions (`internal/rag/prompts/related_question.md`) — this runs after an answer is produced and is not part of query understanding for the current turn.

---

## 9. Generation / Answer Synthesis & Citation

### 9.1 The general concept

The final stage assembles retrieved chunks into a prompt, sends it to an LLM, and — critically for trustworthy RAG — attributes claims in the answer back to specific source chunks so a user can verify them. Context-window budget management (deciding what to keep/trim when retrieved context + conversation history + system prompt exceeds the model's limit) is a core production concern here.

### 9.2 Industry technique variants

Common citation mechanisms: (1) prompting the model to emit inline markers (e.g., `[1]`, `[doc_id]`) referencing a numbered context list; (2) post-hoc attribution — after generation, match each output sentence against the retrieved chunks via embedding similarity to infer likely sources, used as a fallback when the model doesn't cooperate; (3) constrained/structured generation that forces citation fields. Context-fitting commonly uses a sliding-window strategy: always keep the system prompt and the most recent turn, trim older history first.

### 9.3 How RAGFlow does this

**Prompt assembly.** The whole pipeline lives in `ChatPipelineService.AsyncChat` (`internal/service/chat_pipeline.go:207`), implemented as an async pipeline using Go channels — the Python/JS equivalent is an `async def` generator streaming results through a queue. After retrieval (Phase 9), `kbPrompt` (`chat_pipeline.go:2451`) formats each chunk as:

```
ID: 0
├── Title: <doc name>
├── URL: ...
└── Content:
<chunk text>
```

The `ID: N` is the chunk's position in *this prompt's* block list — this exact number is what the model is asked to cite, and is also the index into the final JSON `reference.chunks[N]` array the client receives: a citation marker is a direct array index, not a database row ID. Before formatting, a token-budget pass greedily keeps chunks until `maxTokens * 0.97` is reached (`chat_pipeline.go:2470-2481`). The system prompt's `{knowledge}` placeholder is filled via plain string substitution (`formatPrompt`, `chat_pipeline.go:2516` — essentially Python's `str.format`, not a full templating engine). If citations are enabled, a separate citation-rules block (`internal/rag/prompts/citation_prompt.md`) is appended *after* the token-budget trim, with its own token cost added back in separately when clamping the completion's `max_tokens`.

**Token budget / truncation.** Two copies of the same sliding-window algorithm exist: `s.messageFitIn` (`chat_pipeline.go:2544`) for the plain chat path, and `internal/tokenizer/message_fit.go:51` (`Fit`) for the agent/canvas path. Budget ≈ 95-97% of the model's max/effective context length. Strategy: if everything fits, done; otherwise keep all system messages plus only the last message, dropping older history; if still over budget, trim proportionally — preserving whichever of {system prompt, last message} is smaller, trimming the larger one to fit.

**Citation — two coexisting mechanisms.**

*Standard chat path* (`internal/service/citation.go`): the model is prompted to emit `[ID:i]` markers (max 4 per sentence) referencing the `ID: N` numbers shown above. `RepairBadCitationFormats` (citation.go:351) first normalizes near-miss variants (`(ID: 12)`, `【ID: 12】`, `ref12`) into the canonical form via regex; `ExtractCitationMarkers` then reads off indices the model already wrote — **this is post-hoc regex extraction of a markup convention the LLM was prompted to follow, not an API-level citation feature.** If the model emits *no* markers at all, a fallback (`InsertCitations`, citation.go:68) auto-inserts them: split the answer into sentences, embed each sentence and each candidate chunk, compute cosine similarity, and for each sentence match whichever chunks score within 1% of that sentence's best match at a descending similarity threshold (0.63 → 0.3) — i.e., nearest-neighbor matching between generated sentences and source chunks, used only when the model didn't cooperate with the prompted convention.

*Agentic path* (`internal/agentic_rag/citations.go`): since every tool result the agent reads already carries provenance, the `EvidenceRegistry` (Module 6) stamps each shown passage with a sequential `[ID:n]` handle as it's exposed; the model echoes the handle back, and `ResolveCitations` maps the handle to the real chunk and drops any handle that doesn't resolve to something actually shown — a stricter guarantee than the standard path's position-based extraction, since a dangling/incorrect handle is silently dropped rather than risk pointing at the wrong evidence (compared directly in `internal/agentic_rag/citation_paradigm_compare_test.go`).

In both paradigms, the wire contract to the client is the same: answer text with embedded `[ID:N]` markers, plus a parallel 0-indexed `reference.chunks` JSON array that the frontend resolves `[ID:N]` against to render a clickable citation card.

**Streaming** is implemented: the answer streams as a sequence of result objects over a channel (`chat_pipeline.go:1108+`), serialized by `internal/service/bot_completion.go:98` as `text/event-stream` SSE frames — directly analogous to a FastAPI `StreamingResponse` yielding chunks from an `async for` loop. A streaming-aware filter buffers partial text so a citation marker split across two network chunks isn't rendered or stripped incorrectly.

---

## 10. Advanced Architectures

This module directly compares named industry techniques against what exists in this repo, since this is where RAGFlow's design choices are most distinctive.

### 10.1 RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval)

**General concept:** Sarthi, Abdullah, Tuli, Khanna, Goldie & Manning, ICLR 2024 ([arXiv:2401.18059](https://arxiv.org/abs/2401.18059)). Recursively embed, cluster, and LLM-summarize chunks bottom-up, building a tree with multiple levels of abstraction; retrieval can then pull from whichever tree level best matches the query's level of abstraction (a specific fact vs. a whole-document summary). Reported to improve QuALITY benchmark accuracy by 20 absolute points when paired with GPT-4.

**How RAGFlow does this:** Fully implemented, under the name "tree" compile kind. `internal/ingestion/component/knowledge_compiler/tree/raptor.go` explicitly documents itself as implementing "the 'tree' variant of KnowledgeCompiler: a recursive abstractive summarization tree (RAPTOR)." Clustering uses a custom 1-D "watershed" algorithm over document-ordered chunk embeddings (`watershed.go`, branching factor `tree_order`); each cluster is LLM-summarized (`summarizeTexts`) and the process recurses upward until one root summary remains (`buildTree`). It additionally extracts "claims" per chunk and can cluster on claim-embeddings rather than raw text — an enhancement beyond the vanilla paper. This runs as an optional post-chunking "knowledge compiler" stage selectable per dataset, not as one of the 11 default chunking templates from Module 3.

### 10.2 GraphRAG (Microsoft)

**General concept:** "From Local to Global: A Graph RAG Approach to Query-Focused Summarization" ([arXiv:2404.16130](https://arxiv.org/abs/2404.16130)). Extract an entity-relationship graph from the corpus via LLM prompting, run **Leiden hierarchical community detection** to partition the graph into nested communities, LLM-summarize each community, and answer "global"/sensemaking questions by map-reducing over community summaries (root-level summaries reportedly use 97% fewer tokens than processing raw source text, and outperform plain semantic search on sensemaking questions).

**How RAGFlow does this:** Entity/relationship extraction is real and LLM-driven, via a two-stage prompt (`internal/ingestion/component/knowledge_compiler/structure/prompt.go:215-345`): stage 1 extracts entities as JSON (`{type, name, description, source_chunk_ids}`); stage 2 is fed the stage-1 entity names and may only connect "Known Entities" — the classic GraphRAG node-then-edge extraction order. RAGFlow's own schema (`internal/ingestion/knowledge_compile/templates/knowledge_graph.yaml`) defines fixed entity types (person/org/product/regulation/location/other) and relation types (owns/part_of/caused_by/regulates/located_in/other) rather than an open schema. There is **no dedicated graph database** — entities and relations are stored as ordinary rows in the same document index (ES/Infinity/etc.), tagged via a `knowledge_graph_kwd` field (`"entity"`/`"relation"`). Retrieval-time graph usage exists in two separate mechanisms: (A) `graph_explore`, an agentic ReAct tool (`internal/agentic_rag/kg_service.go:176-497`) that seeds top-matching entities, hops out N relation levels, and returns a subgraph plus up to 6 cited source passages; (B) `internal/service/graph/pipeline.go` (explicitly commented as mirroring the old Python `rag/graphrag/search.py::KGSearch`), an always-on local-search path used in regular chat answering that does entity/relation/N-hop-path search with PageRank-style weighting plus community-report lookup, injecting the result as one synthetic chunk into the normal retrieval context. **Important gap found:** the pipeline *reads* rows tagged `community_report`, but no code anywhere in `internal/` *writes/generates* them — there is no Leiden/Louvain clustering algorithm in the Go codebase (confirmed by exhaustive grep). This strongly suggests community-report generation (the actual Microsoft-GraphRAG-defining step) either was never ported into this Go rewrite, or is produced by a legacy out-of-tree Python component — the consumption path exists, but the production path does not, in this codebase.

### 10.3 Self-RAG

**General concept:** Asai, Wu, Wang, Sil & Hajishirzi, ICLR 2024 Oral ([arXiv:2310.11511](https://arxiv.org/abs/2310.11511)). A model is *trained* to emit special reflection tokens (`Retrieve`, `IsRel`, `IsSup`, `IsUse`) interleaved with generation, letting it adaptively decide when retrieval is even necessary and self-critique whether its own output is supported by retrieved passages — this requires a specially fine-tuned base model, not just prompting.

**How RAGFlow does this:** **Not found, and could not be, by construction** — Self-RAG requires training-time changes to the base model (special tokens, a critic model), and RAGFlow only calls out to off-the-shelf hosted/self-hosted LLMs through a provider API (Module 4/9); it never fine-tunes a model. This is an explicit, structural gap, not merely an unimplemented feature.

### 10.4 Corrective RAG (CRAG)

**General concept:** Yan, Gu, Zhu & Ling ([arXiv:2401.15884](https://arxiv.org/abs/2401.15884)). A lightweight retrieval evaluator scores retrieved documents as Correct/Incorrect/Ambiguous; on Incorrect/Ambiguous, the system triggers corrective actions such as falling back to web search and decomposing/recomposing documents to isolate key information, rather than blindly trusting whatever the retriever returned.

**How RAGFlow does this:** Not implemented as a named "evaluate-then-correct" mechanism, but **two related capabilities exist that approximate pieces of it**: (1) `DeepResearcher`'s sufficiency check (`internal/service/deep_researcher.go`) is conceptually a retrieval-quality evaluator — it judges whether accumulated evidence is sufficient and, if not, generates follow-up sub-queries and re-retrieves, which is CRAG's "Ambiguous → refine" branch in spirit, though it doesn't explicitly classify Correct/Incorrect/Ambiguous the way the paper does; (2) the agentic ReAct loop's `web_search` tool gives the LLM a corrective fallback to the open web when internal search is unsatisfying, similar in spirit to CRAG's web-search fallback for Incorrect retrievals, but the decision to use it is left to open-ended LLM judgment via tool-calling rather than a dedicated scored evaluator component.

### 10.5 Agentic RAG

**General concept:** Instead of a fixed single retrieve-then-generate pass, the LLM is given tools (search, filters, web, calculators, etc.) and autonomy to plan which to call, iterate, and decide when it has enough evidence — effectively turning retrieval into a ReAct-style agent loop rather than a pipeline stage.

**How RAGFlow does this:** This is RAGFlow's most fully-realized advanced architecture — see the full description in Module 6.3 (`internal/agentic_rag/`, built on `eino`'s ADK framework) and the agent/workflow canvas in Module 10.6 below. It is a production-grade implementation of this pattern: tool-calling loop with iteration caps, parallel same-round tool execution, evidence-tracked citations, and a deterministic fallback-answer guarantee.

### 10.6 Agent orchestration: the RAGFlow "canvas"

Beyond agentic retrieval specifically, RAGFlow has a general visual workflow builder ("canvas") for composing arbitrary pipelines of LLM calls, tools, and retrieval steps — conceptually similar to LangGraph's `StateGraph` or a Dify/n8n-style flowchart builder.

- A **Canvas** (`internal/agent/canvas/canvas.go:47`) is an adjacency-list graph: `{components: {id: {obj: {component_name, params}, downstream, upstream}}}` — a plain dict-of-dicts DAG spec, the same shape a LangGraph definition or Airflow DAG would take.
- `Compile` (`internal/agent/canvas/compile.go:152`) turns this into a `compose.Runnable` using ByteDance's `eino` graph library — Go's rough equivalent of LangChain's LCEL/LangGraph runner. Construction happens in passes: expand `Loop`/`Parallel` macro-nodes into sub-workflows, register every component as a graph node with pre/post state hooks, wire edges from the DSL's upstream/downstream lists, install conditional routing for `Switch`/`Categorize` nodes, then connect loose ends to `START`/`END`. The graph is **strictly acyclic** — `eino` rejects cycles at compile time, and the frontend also enforces no-cycle edges — so "loops" are implemented as an explicit macro-expansion (sub-workflow with a loop-termination condition), not a true graph cycle.
- **Branching**: `Categorize` (LLM-based classifier choosing one of several configured categories) and `Switch` (pure rule-based AND/OR condition router) both feed a `MultiBranch` gate that, at runtime, only executes the chosen child.
- **Loops/parallelism**: `loop_subgraph.go`/`parallel_subgraph.go` collapse a `Loop`/`Parallel` node's body into one opaque sub-workflow node, with a termination condition or an items-list to fan out over (comparable to `asyncio.gather` over a bounded worker pool).
- **Checkpointing/resumability**: implemented end-to-end via Kvrocks-backed checkpoint storage (`checkpoint_store.go`) and `compose.Interrupt`/`compose.ResumeWithData` (`interrupt_resume.go`) — a `UserFillUp` node (a canvas form awaiting human input) can pause a running workflow mid-graph, persist a checkpoint, and resume exactly where it left off once the user responds, without re-running upstream side effects.
- **Retrieval integration**: confirmed via a dedicated `Retrieval` canvas component (`internal/agent/component/universe_a_wrappers.go:159-175`, internally named `search_my_dateset` — a preserved typo from the original Python DSL for backward compatibility), which wires into the same underlying search service used by the plain chat pipeline (Module 6) through a dependency-injected interface set up at process startup (`internal/server/api/server.go:170,194`) — architecturally like registering a concrete implementation against a Python `Protocol`/ABC at app-init time, to avoid an import cycle between the lower-level canvas package and the higher-level service package.

---

## 11. Evaluation of RAG Systems

### 11.1 The general concept

A complete RAG evaluation separates **retrieval quality** from **generation quality**:

- **Retrieval metrics** (classic information retrieval): Precision@k (fraction of top-k retrieved items that are relevant), Recall@k (fraction of all relevant items captured in top-k), Mean Reciprocal Rank — MRR (average of 1/rank of the first relevant result), NDCG (Normalized Discounted Cumulative Gain — rewards relevant results appearing earlier, weighted by graded relevance).
- **Generation metrics**: faithfulness/groundedness (does the answer's claims hold up against the retrieved context, independent of whether the context itself was correct?), answer relevance (does the answer address the question asked?), context precision/recall (how much of the retrieved context was actually useful, and how much of the needed information was retrieved at all).

### 11.2 Industry evaluation frameworks (primary sources)

| Framework | Core metrics | Source |
| --- | --- | --- |
| **RAGAS** | Faithfulness, Answer Relevancy, Context Precision, Context Recall | [docs.ragas.io](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/) |
| **TruLens RAG Triad** | Context Relevance, Groundedness, Answer Relevance — three LLM-judged evaluations that together give confidence the app is free of hallucination | [trulens.org RAG Triad](https://www.trulens.org/getting_started/core_concepts/rag_triad/) |
| **DeepEval** | 5 RAG metrics: generator-focused (Answer Relevancy, Faithfulness) + retriever-focused (Contextual Relevancy, Contextual Precision, Contextual Recall); can also import RAGAS metrics directly | [deepeval.com](https://deepeval.com/docs/getting-started-rag) |
| **ARES** (Stanford) | Context relevance, answer faithfulness, answer relevance, scored via fine-tuned lightweight LM judges plus prediction-powered inference (PPI) calibration against a small human-labeled sample, rather than relying on a single large LLM judge | Saad-Falcon, Khattab, Potts & Zaharia, NAACL 2024, [arXiv:2311.09476](https://arxiv.org/abs/2311.09476) |

### 11.3 How RAGFlow does this

**Clear finding: there is no genuine RAG-quality evaluation framework anywhere in this codebase.** This was checked exhaustively — grep across `internal/` and `test/` for precision/recall/NDCG/MRR/F1/RAGAS/faithfulness/hallucination/ground_truth/golden-dataset, with every hit manually inspected. What actually exists:

1. **`test/benchmark/`** — a load/throughput benchmark, not a quality benchmark. `test/benchmark/metrics.py` computes only latency statistics (avg/min/p50/p90/p95) and QPS/success-rate. The project's own `test/benchmark/README.md` is explicit about this limitation: *"Completion measures protocol success, not answer quality... An empty retrieval result with `code: 0` is a successful API request, not evidence of good retrieval quality."*
2. **`internal/agentic_rag/retrieval_serve_log.go`** — per-chunk debug logging ("did the sentence carrying the answer ever reach the model?") intended for manual human root-causing of a wrong answer, never aggregated into a score.
3. **`internal/agentic_rag/citation_paradigm_compare_test.go`** — despite the name, this is a deterministic unit/regression test asserting exact string-parsing behavior between two citation formats, not a quantitative quality comparison.
4. **`internal/ingestion/component/knowledge_compiler/golden/metrics.go`** — checks *structural* well-formedness of a compiled RAPTOR tree (every node has a parent, every node has a vector, all source chunks represented) — a correctness/completeness check on the compiler's own output shape, not a semantic-quality evaluation of whether the summaries are good.
5. Everything else that superficially matched the search terms was a false positive: floating-point "precision" in unrelated numeric code, "recall" used as an engineering verb meaning "fetch candidates," OCR bounding-box "precision," an anti-hallucination instruction embedded in an extraction *prompt* (a guardrail, not a hallucination *detector*), and literal sample prose used as chunker test fixtures.

**Practical implication for a team using/extending RAGFlow:** there is no built-in way to measure, as a number you could track over time or A/B test, whether a retrieval-config change or a chunking-strategy change improved or hurt answer quality. Building that layer — e.g., wiring in RAGAS or a custom LLM-judge harness against a labeled query set — would be new work on top of this repo, not something you'd be turning on.

---

## 12. Production Best Practices

These are general industry practices; items are cross-referenced to the relevant RAGFlow module above where RAGFlow implements (or does not implement) them.

- **Long-document handling.** Hierarchical/parent-child chunking (Module 3) and document-layout-aware chunking (titles/sections, Module 2-3) are the standard answers to "a 300-page PDF doesn't fit in one chunk, and a flat fixed-size split loses structure." RAGFlow implements both: layout-driven heading hierarchies (`book`/`laws`/`paper` templates) and genuine parent/child chunk materialization (`children_delimiters`, Module 3.3).
- **Metadata filtering.** Scoping retrieval by tags/dates/source before or alongside similarity scoring avoids returning plausible-but-wrong-scope results (e.g., last year's pricing doc). RAGFlow implements this with pushdown-to-engine filtering and three selection modes (auto/semi_auto/manual) (Module 6.3).
- **Deduplication.** Not specifically investigated in this research pass as a named feature; nothing described above addresses chunk- or document-level deduplication explicitly — treat as unverified rather than assumed absent.
- **Chunk-overlap tuning.** A standard lever (overlap preserves context across a split boundary at the cost of redundant storage/compute). RAGFlow exposes `overlapped_percent` as a configurable chunker parameter (Module 3.3).
- **Tables and images.** Dedicated table-structure-recognition reconstructing scanned tables into real HTML, and a vision-model-based picture parser treating whole images as one chunk, rather than discarding non-text content (Module 2.3).
- **Citation and hallucination mitigation.** Two production-grade mechanisms: prompted citation markers checked against what the model was actually shown (agentic path), with embedding-similarity fallback matching for the standard path when the model doesn't cooperate (Module 9.3). Note this is a mitigation, not a guarantee — the standard path's fallback is itself a heuristic (nearest-neighbor sentence matching), and RAGFlow has no Self-RAG-style trained critique mechanism (Module 10.3) or a CRAG-style retrieval-quality gate (Module 10.4) that would catch a bad retrieval *before* generation.
- **Latency/cost tradeoffs.** Embedding caching keyed per-chunk (avoids re-paying for unchanged content on retry), batched embedding calls, and a reranking-pagination restriction that keeps the expensive cross-encoder pass to a single top-k call are all present (Modules 4.3, 7.3). Shared cross-worker rate-limit cooldowns (Module 4.3) prevent a thundering-herd 429 storm across concurrent ingestion workers.
- **Guardrails/monitoring/observability.** RAGFlow has per-chunk debug logging for root-causing bad answers (Module 11.3) and per-tool telemetry (call counts, errors, durations) in the agentic loop (Module 6.3), but — per Module 11 — nothing that aggregates into a trackable quality metric or alerting signal; this would need to be built by an adopting team.

---

## 13. Gaps — What RAGFlow Does NOT Do

Stated plainly, so you know what's industry-standard-but-absent here, based on what the code-reading agents could and could not find:

- **Self-RAG** (Module 10.3) — structurally impossible without fine-tuning the base model; RAGFlow only calls external/self-hosted LLM APIs, never trains one.
- **A named Corrective-RAG retrieval-quality gate** (Module 10.4) — pieces exist (DeepResearcher's sufficiency check, the agent's `web_search` fallback tool) but there is no dedicated Correct/Incorrect/Ambiguous classifier driving a corrective branch the way the CRAG paper describes.
- **HyDE** (Module 8.3) — confirmed absent by exhaustive grep; query embeddings are always computed from the (possibly keyword-augmented/translated) raw question, never from an LLM-generated hypothetical answer.
- **Anthropic-style Contextual Retrieval** (chunk-level LLM-generated context prepended before embedding/BM25 indexing) (Module 8.3) — not found in the ingestion pipeline.
- **Reciprocal Rank Fusion (RRF)** (Module 6.3) — all hybrid-search combination logic found is a linear weighted sum of normalized scores, never RRF.
- **Semantic (embedding-similarity-based) chunk splitting** (Module 3.3) — no chunker decides split points via adjacent-sentence embedding distance; RAPTOR's clustering happens after chunking, as a separate post-processing stage, not as the chunking mechanism itself.
- **Late chunking** (Jina AI's "embed-the-whole-document-first, pool-per-chunk-after" technique, Module 3.2) — not found; embedding happens per-chunk after chunking, in the conventional chunk-then-embed order.
- **GraphRAG community-report *generation*** (Module 10.2) — the consumption path (reading `community_report`-tagged rows at query time) exists, but no Leiden/Louvain or any other graph-community-detection algorithm was found anywhere in `internal/` that would actually produce those rows; this looks like an incompletely-ported or externally-sourced feature.
- **`resume` (CV/résumé) chunking mode** (Module 3.3) — present in the original Python RAGFlow's parser-mode list, not found anywhere in this Go rewrite.
- **Any genuine RAG-quality evaluation framework** (Module 11.3) — no RAGAS/TruLens/DeepEval/ARES-equivalent, no precision/recall/NDCG/MRR computation against a labeled or LLM-judged dataset anywhere in the repo. Only load/throughput benchmarking and debug logging exist.
- **Dataset-level chunk deduplication** — not confirmed present or absent; outside the scope of what this research pass verified, so treat as an open question rather than a confirmed gap.

---

## 14. References

### General RAG / industry sources (web, primary sources)

- Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS 2020. [arXiv:2005.11401](https://arxiv.org/abs/2005.11401)
- Sarthi, P. et al. (2024). *RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval.* ICLR 2024. [arXiv:2401.18059](https://arxiv.org/abs/2401.18059) · [GitHub](https://github.com/parthsarthi03/raptor)
- Edge, D. et al. / Microsoft Research (2024). *From Local to Global: A Graph RAG Approach to Query-Focused Summarization.* [arXiv:2404.16130](https://arxiv.org/abs/2404.16130) · [Microsoft Research blog](https://www.microsoft.com/en-us/research/blog/graphrag-new-tool-for-complex-data-discovery-now-on-github/) · [GraphRAG docs: default dataflow](https://microsoft.github.io/graphrag/index/default_dataflow/)
- Asai, A. et al. (2024). *Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection.* ICLR 2024 (Oral). [arXiv:2310.11511](https://arxiv.org/abs/2310.11511) · [project site](https://selfrag.github.io/)
- Yan, S-Q. et al. (2024). *Corrective Retrieval Augmented Generation.* [arXiv:2401.15884](https://arxiv.org/abs/2401.15884) · [GitHub](https://github.com/HuskyInSalt/CRAG/)
- Gao, L., Ma, X., Lin, J., Callan, J. (2023). *Precise Zero-Shot Dense Retrieval without Relevance Labels (HyDE).* ACL 2023. [arXiv:2212.10496](https://arxiv.org/abs/2212.10496) · [ACL Anthology](https://aclanthology.org/2023.acl-long.99/)
- Anthropic (2024). *Introducing Contextual Retrieval.* [anthropic.com/engineering/contextual-retrieval](https://www.anthropic.com/engineering/contextual-retrieval)
- Cormack, G.V., Clarke, C.L.A., Buettcher, S. (2009). *Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods.* SIGIR 2009. [Google Research](https://research.google/pubs/reciprocal-rank-fusion-outperforms-condorcet-and-individual-rank-learning-methods/)
- Cohere. *Rerank overview documentation.* [docs.cohere.com/docs/rerank-overview](https://docs.cohere.com/docs/rerank-overview)
- Pinecone. *Chunking Strategies for LLM Applications.* [pinecone.io/learn/chunking-strategies](https://www.pinecone.io/learn/chunking-strategies/)
- LlamaIndex. *SentenceWindowNodeParser* / *Hierarchical node parser* API docs. [sentence_window](https://developers.llamaindex.ai/python/framework-api-reference/node_parsers/sentence_window/) · [hierarchical](https://developers.llamaindex.ai/python/framework-api-reference/node_parsers/hierarchical/)
- Jina AI (2024). *Late Chunking in Long-Context Embedding Models.* [jina.ai/news/late-chunking-in-long-context-embedding-models](https://jina.ai/news/late-chunking-in-long-context-embedding-models/)
- RAGAS documentation. *Context Precision* and related metrics. [docs.ragas.io](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/)
- TruLens documentation. *RAG Triad.* [trulens.org/getting_started/core_concepts/rag_triad](https://www.trulens.org/getting_started/core_concepts/rag_triad/)
- DeepEval documentation. *RAG Evaluation Quickstart.* [deepeval.com/docs/getting-started-rag](https://deepeval.com/docs/getting-started-rag)
- Saad-Falcon, J., Khattab, O., Potts, C., Zaharia, M. (2024). *ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems.* NAACL 2024. [arXiv:2311.09476](https://arxiv.org/abs/2311.09476) · [GitHub](https://github.com/stanford-futuredata/ARES)

### RAGFlow repository files cited (Go unless noted; all paths relative to repo root)

**Parsing/ingestion (Module 2):** `internal/utility/file.go`, `internal/parser/parser/parser_type.go`, `internal/ingestion/component/parser_dispatch.go`, `internal/parser/parser/pdf_parser_common.go`, `internal/parser/parser/tcadp_common.go`, `internal/deepdoc/parser/pdf/parse_cgo.go`, `internal/deepdoc/parser/pdf/pdfium/pdfium.go`, `internal/deepdoc/parser/pdf/parser.go`, `internal/deepdoc/native/det.go`, `internal/deepdoc/native/ocr_rec.go`, `internal/deepdoc/native/dla.go`, `internal/deepdoc/native/tsr.go`, `internal/deepdoc/native/session.go`, `internal/deepdoc/parser/pdf/table/table_html.go`, `internal/deepdoc/parser/pdf/layout/` (combined_column.go, dehyphen.go, toc_header_footer.go), `internal/deepdoc/parser/office/engine_cgo.go`, `internal/deepdoc/parser/office/engine_nocgo.go`, `internal/deepdoc/parser/office/office_detect.go`, `internal/deepdoc/parser/office/parser.go`, `internal/parser/parser/xlsx_parser.go`, `internal/parser/parser/xls_parser.go`, `internal/agent/tool/crawler.go`, `tools/firecrawl/firecrawl_connector.py` (Python, standalone), `internal/common/constants.go`, `internal/common/task.go`, `internal/service/ingestion_task_service.go`, `internal/service/ingestion_event.go`, `internal/ingestion/service/ingestion_service.go`, `internal/ingestion/task/pipeline_executor.go`, `internal/ingestion/pipeline/pipeline.go`, `internal/ingestion/task/chunk_index_writer.go`.

**Chunking (Module 3):** `internal/ingestion/pipeline/template/ingestion_pipeline_*.json`, `internal/ingestion/pipeline/builtin_registry.go`, `internal/ingestion/component/chunker/general.go`, `qa.go`, `manual.go`, `table.go`, `title.go`, `page.go`, `one.go`, `token.go`, `internal/ingestion/component/schema/chunker.go`, `internal/ingestion/pipeline/component_params.go`, `internal/ingestion/component/extractor_tag.go`, `tag_source.go`, `tag_query.go`.

**Embedding (Module 4):** `internal/entity/models/types.go`, `builtin.go`, `openai.go`, `cohere.go`, `jina.go`, `voyage.go`, `model.go`, `conf/models/*.json`, `internal/service/model_factory.go`, `internal/ingestion/component/tokenizer.go`, `internal/ingestion/task/embedder.go`, `internal/ingestion/chunkcache/chunkcache.go`, `internal/service/nlp/retrieval.go` (`GetVector`).

**Indexing/storage (Module 5):** `internal/engine/engine.go`, `internal/engine/global.go`, `conf/mapping.json`, `internal/engine/elasticsearch/client.go`, `chunk.go`, `internal/ingestion/component/schema/chunk_types.go`, `conf/infinity_mapping.json`, `internal/engine/infinity/chunk.go`, `internal/storage/types.go`, `internal/storage/storage_factory.go`.

**Retrieval/reranking/query understanding (Modules 6-8):** `internal/service/nlp/retrieval.go`, `internal/service/nlp/reranker.go`, `internal/service/similarity_weight.go`, `internal/service/metadata_filter.go`, `internal/engine/elasticsearch/meta_filter.go`, `internal/agentic_rag/agent.go`, `tool_grep_chunks.go`, `tool_search_bm25_chunks.go`, `tool_search_semantic_chunks.go`, `tool_search_chunks.go`, `tool_list_chunks.go`, `tool_search_metadata.go`, `tool_graph_explore.go`, `evidence_registry.go`, `kg_service.go`, `conf/agentic_rag.yaml`, `internal/service/deep_researcher.go`, `internal/service/generator.go`, `internal/rag/prompts/keyword_prompt.md`, `meta_filter.md`, `cross_languages_sys_prompt.md`, `cross_languages_user_prompt.md`, `internal/service/related_question.go`, `internal/rag/prompts/related_question.md`.

**Generation/citation (Module 9):** `internal/service/chat_pipeline.go`, `internal/service/citation.go`, `internal/agentic_rag/citations.go`, `citation_paradigm_compare_test.go`, `internal/tokenizer/message_fit.go`, `internal/agent/chat/message_fit.go`, `internal/rag/prompts/citation_prompt.md`, `internal/service/bot_completion.go`.

**Agent orchestration / canvas, GraphRAG, RAPTOR (Module 10):** `internal/agent/canvas/canvas.go`, `compile.go`, `scheduler.go`, `multibranch.go`, `loop_subgraph.go`, `parallel_subgraph.go`, `checkpoint_store.go`, `interrupt_resume.go`, `internal/agent/component/categorize.go`, `switch.go`, `agent.go`, `universe_a_wrappers.go`, `internal/agent/tool/retrieval.go`, `retrieval_service.go`, `internal/server/api/server.go`, `internal/ingestion/component/knowledge_compiler/structure/prompt.go`, `structure.go`, `internal/ingestion/component/knowledge_compiler/tree/raptor.go`, `watershed.go`, `internal/ingestion/knowledge_compile/templates/knowledge_graph.yaml`, `internal/service/graph/pipeline.go`, `search.go`, `types.go`, `internal/service/dataset_structure_graph.go`, `internal/engine/elasticsearch/kg_test.go`.

**Evaluation (Module 11):** `test/benchmark/metrics.py`, `test/benchmark/README.md`, `internal/agentic_rag/retrieval_serve_log.go`, `citation_paradigm_compare_test.go`, `internal/ingestion/component/knowledge_compiler/golden/metrics.go`, `golden_test.go`, `test/testcases/restful_api/test_retrieval.py`, `test/integration/wiki/test_wiki_incremental.py`.
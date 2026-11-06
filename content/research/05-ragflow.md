---
title: RAGFlow, source notes
summary: Which RAGFlow files back each claim in the case-study track, the papers and docs behind the general ideas, and what we could not settle.
time: 15 min
---

Source: https://github.com/infiniflow/ragflow at commit `eabad0c74c73bfa74e218c1fb751da68c1914833` (15 October 2026), on `main`. Read locally, not run. Research dates: 2026-11-05 and 2026-11-06.
Rule used here: claims in the [case-study track](lesson:ragflow/tour) were checked against the code at that commit. "Not found" means a search of `internal/` (and `test/` where stated) found nothing. It is not proof of absence.

## 1. What this checkout is

A Go rewrite of the server. The old Python packages (`api/`, `rag/`, `deepdoc/`, `graphrag/`) are now Go packages under `internal/`. Python remains in `sdk/python`, `test/` and a few scripts under `tools/`. Many Go files name the Python file they were ported from in a comment.

All paths below are relative to the repo root. Prefix `https://github.com/infiniflow/ragflow/blob/eabad0c74c73bfa74e218c1fb751da68c1914833/` to open one.

## 2. Files by topic

**Parsing.** `internal/utility/file.go` (extension to type), `internal/parser/parser/parser_type.go` (parser factory), `internal/ingestion/component/parser_dispatch.go`, `internal/parser/parser/pdf_parser_common.go` (PDF methods: deepdoc, plain_text, mineru, paddleocr, docling, opendataloader, somark, tcadp), `internal/deepdoc/parser/pdf/parser.go` (per-page OCR decision), `internal/deepdoc/native/det.go` (DB text detector port), `internal/deepdoc/native/ocr_rec.go` (CTC recognizer, 48 px line height, 6,625-entry dictionary), `internal/deepdoc/native/dla.go` (YOLOv10 layout), `internal/deepdoc/native/tsr.go` (table structure), `internal/deepdoc/parser/pdf/table/table_html.go`, `internal/deepdoc/native/session.go` (shared ONNX runtime), `internal/deepdoc/parser/pdf/layout/` (columns, de-hyphenation, header/footer/TOC removal), `internal/deepdoc/parser/office/` (Office files via a Rust library over cgo; format sniffing), `internal/parser/parser/xlsx_parser.go`, `xls_parser.go`.

**Indexing jobs.** `internal/common/constants.go` (task states), `internal/common/task.go` (NATS subject), `internal/service/ingestion_task_service.go` (producer), `internal/ingestion/task/pipeline_executor.go` (consumer; parent chunk materialization), `internal/ingestion/pipeline/pipeline.go` (pipeline graph, progress reporting, at most one Extractor), `internal/ingestion/task/chunk_index_writer.go`.

**Chunking.** `internal/ingestion/pipeline/template/ingestion_pipeline_*.json` (12 templates: audio, book, email, general, laws, manual, one, paper, picture, presentation, qa, table), `internal/ingestion/pipeline/builtin_registry.go`, `internal/ingestion/component/chunker/` (`general.go`, `qa.go`, `manual.go`, `table.go`, `title.go`, `page.go`, `one.go`, `token.go`), `internal/ingestion/component/schema/chunker.go` (`chunk_token_size` 512, `overlapped_percent` 0 in [0, 90], `children_delimiters`, `table_context_size`, `image_context_size`).

**Extras per chunk.** `internal/ingestion/component/extractor.go` (keywords, questions, summary, metadata, run concurrently), `extractor_tag.go`, `tag_source.go`, `tag_query.go`. `internal/ingestion/component/schema/chunk_types.go` (`ContextualText` = context above + text + context below).

**Embedding.** `internal/entity/models/types.go` (`ModelDriver` interface), provider files in `internal/entity/models/`, `internal/entity/models/builtin.go` (local TEI server), `conf/models/*.json` (model catalog), `internal/ingestion/component/tokenizer.go` (`embedChunks`, `q_<n>_vec` naming, title/content vector blend), `internal/ingestion/task/embedder.go` (batching, shrink-and-retry, shared 429 cooldown), `internal/ingestion/chunkcache/chunkcache.go` (7-day TTL), `internal/service/nlp/retrieval.go` (`GetVector` with `Query: true`).

**Storage.** `internal/engine/engine.go` (`DocEngine`, `MessageQueue`), `internal/engine/global.go`, `conf/mapping.json` (Elasticsearch field-suffix mapping; `q_*_vec` as cosine `dense_vector`), `internal/engine/elasticsearch/chunk.go`, `conf/infinity_mapping.json`, `internal/engine/infinity/chunk.go` (HNSW `M=16`, `ef_construction=50`, LVQ encoding), `internal/storage/types.go`, `storage_factory.go` (MinIO, S3, OSS, GCS).

**Search and rerank.** `internal/service/nlp/retrieval.go` (defaults: vector weight 0.3, or 1.0 when vector-only; similarity threshold 0.2; 64 rerank candidates; no paging with a rerank model; `weighted_sum` fusion for Infinity; `"0.001,1"` for other engines), `internal/service/nlp/reranker.go` (`RerankByModel`, `NormalizeRerankScores`, `RerankStandard`, `HybridSimilarity`, `TokenSimilarity`), `internal/service/similarity_weight.go`, `internal/service/metadata_filter.go`.

**Question rewriting and answers.** `internal/service/chat_pipeline.go` (rewrite order, `kbPrompt`, 97% token budget, history fitting, streaming), `internal/service/generator.go`, `internal/rag/prompts/` (`keyword_prompt.md`, `meta_filter.md`, `cross_languages_*`, `citation_prompt.md`, `related_question.md`), `internal/service/citation.go` (`RepairBadCitationFormats`, `ExtractCitationMarkers`, `InsertCitations` with 0.63 → 0.3 threshold), `internal/tokenizer/message_fit.go`, `internal/service/bot_completion.go` (SSE).

**Agentic RAG.** `internal/agentic_rag/agent.go` (default 120 iterations, `finalizeAnswer`), `tool_*.go`, `evidence_registry.go`, `citations.go`, `citation_paradigm_compare_test.go`, `kg_service.go`, `retrieval_serve_log.go`, `internal/service/deep_researcher.go` (max depth 3).

**Trees, graphs, canvas.** `internal/ingestion/component/knowledge_compiler/tree/raptor.go`, `watershed.go`, `claims.go`, `internal/ingestion/component/knowledge_compiler/structure/prompt.go` (entity then relation extraction), `internal/ingestion/knowledge_compile/templates/knowledge_graph.yaml`, `internal/service/graph/` (`search.go`, `retrieval.go` read `community_report`), `internal/agent/canvas/` (`canvas.go`, `compile.go`, `scheduler.go`, `loop_subgraph.go`, `parallel_subgraph.go`, `checkpoint_store.go`, `interrupt_resume.go`), `internal/agent/component/`.

**Evaluation.** `test/benchmark/metrics.py` and `test/benchmark/README.md` (latency and success rate only), `internal/ingestion/component/knowledge_compiler/golden/metrics.go` (checks the tree's shape, not its quality).

## 3. Papers and docs behind the general ideas

- Lewis et al. 2020, RAG: https://arxiv.org/abs/2005.11401
- Liu et al. 2023, Lost in the Middle: https://arxiv.org/abs/2307.03172
- Cormack, Clarke, Buettcher 2009, Reciprocal Rank Fusion: https://research.google/pubs/reciprocal-rank-fusion-outperforms-condorcet-and-individual-rank-learning-methods/
- Gao et al. 2023, HyDE: https://arxiv.org/abs/2212.10496
- Anthropic 2024, Contextual Retrieval: https://www.anthropic.com/engineering/contextual-retrieval
- Nogueira et al. 2019, doc2query: https://arxiv.org/abs/1904.08375
- Sarthi et al. 2024, RAPTOR: https://arxiv.org/abs/2401.18059
- Edge et al. 2024, GraphRAG: https://arxiv.org/abs/2404.16130
- Asai et al. 2024, Self-RAG: https://arxiv.org/abs/2310.11511
- Yan et al. 2024, Corrective RAG: https://arxiv.org/abs/2401.15884
- Malkov and Yashunin, HNSW: https://arxiv.org/abs/1603.09320
- Kusupati et al. 2022, Matryoshka embeddings: https://arxiv.org/abs/2205.13147
- Formal et al. 2021, SPLADE: https://arxiv.org/abs/2107.05720
- Khattab and Zaharia 2020, ColBERT: https://arxiv.org/abs/2004.12832
- Saad-Falcon et al. 2024, ARES: https://arxiv.org/abs/2311.09476
- Pinecone, chunking strategies: https://www.pinecone.io/learn/chunking-strategies/
- LlamaIndex, sentence window and hierarchical node parsers: https://developers.llamaindex.ai/python/framework-api-reference/node_parsers/sentence_window/
- Jina AI, late chunking: https://jina.ai/news/late-chunking-in-long-context-embedding-models/
- RAGAS: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/
- TruLens RAG triad: https://www.trulens.org/getting_started/core_concepts/rag_triad/
- DeepEval RAG quickstart: https://deepeval.com/docs/getting-started-rag
- Cohere rerank overview: https://docs.cohere.com/docs/rerank-overview

## 4. What we could not settle

- Whether RAGFlow removes duplicate chunks or documents. Not investigated.
- Where community reports come from. The search code reads them; nothing in `internal/` writes them; no Leiden or Louvain code was found.
- The Python version's `resume` chunking mode. Not found in the Go code.
- How the Elasticsearch path normalizes the engine's own scores before the Go-side blend. We traced the Go-side blend (`HybridSimilarity`, `TokenSimilarity`, both 0 to 1) but not every engine path.
- Anything about runtime behavior, speed or answer quality. We read the code and did not run it.
- The paper results quoted in the RAG track (RAPTOR's 20-point gain, Anthropic's failure rates) are the authors' numbers. We did not reproduce them.

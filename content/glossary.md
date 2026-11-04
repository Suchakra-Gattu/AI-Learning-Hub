---
title: Plain-words glossary
summary: Every hard word in the course, said simply. If a word is missing, add it.
---

**Agent**: A language model inside a harness, so it can take actions and see the results, not only write text. See [what a harness is](lesson:harness/what-is-a-harness).
**Append-only**: A record you only ever add to at the end. You never edit or delete old lines. Good for logs.
**Approval**: A human saying "yes, do that" before a risky action runs.
**BM25**: A well-known way to rank text by matching words. Rare words count more, and long texts do not win just for being long. See [retrieval](lesson:rag/retrieval-that-works).
**Bundle**: In DeepSeek Harness, a group of plugins and their settings that ship together.
**Cache**: A saved answer, so the same question next time costs nothing. Clear it when the data changes.
**Chunk**: One piece of a document that you store and search on its own. See [chunking](lesson:rag/chunking).
**Citation**: A pointer in an answer to the source it came from, such as [1].
**Compaction**: Replacing the old part of a long conversation with a short summary to save room.
**Context window**: The most text a model can read in one request.
**Cordis**: The open-source plugin framework that DeepSeek Harness is built on.
**Cosine similarity**: A score for how alike two lists of numbers are, by the direction they point. 1 is the same, near 0 is unrelated.
**Embedding**: A list of numbers that stands for the meaning of a piece of text. See [embeddings](lesson:rag/embeddings-and-vectors).
**Eval set**: A list of questions with known right answers, run after every change to check quality. See [measure quality](lesson:rag/measure-quality).
**Garbage in, garbage out**: If the text going in is bad, the answers coming out are bad.
**Guardrail**: A rule or check that keeps a system inside safe limits.
**Hallucination**: When a model states something that is not true as if it were. A plain word for it is "making things up".
**Harness**: Everything around a model that lets it act safely: the loop, tools, permissions, memory, and log. See [what a harness is](lesson:harness/what-is-a-harness).
**Hash**: A short fingerprint of some text. If the text changes, the hash changes. Used to spot changed documents.
**Hook**: A named moment in a program where your own code can step in, such as "before a tool runs".
**Hybrid search**: Running keyword search and vector search together and merging the results.
**Index**: Where chunks are stored so they can be found fast.
**Injection (prompt injection)**: Text the model reads that contains instructions, which the model then follows. See [safety](lesson:rag/fast-cheap-safe).
**JSON**: A plain text way to write structured data, like `{"name": "tent"}`.
**JSONL**: A file with one JSON object on each line. Handy for logs.
**Keyword search**: Finding text by matching the words in it.
**Language model**: A program that predicts text. Give it text, it gives text back.
**Log**: A record of what happened, in order.
**Metadata**: Information about the text, such as its file name, date, or who may see it.
**MRR**: Mean reciprocal rank. One score for how high the right chunk ranks. 1.0 means always first.
**OCR**: Reading text from a picture, such as a scanned page.
**Overlap**: Repeating a little text between neighboring chunks so an idea cut at the edge appears whole in one.
**Permission**: A rule saying whether an action is allowed, needs a yes, or is blocked.
**Plugin**: A piece of code that adds a capability to a larger program and can be loaded or removed.
**POC**: Proof of concept. A quick build that shows an idea can work.
**Profile**: In DeepSeek Harness, a named recipe of which plugins to run.
**Prompt**: The text sent to a model. In RAG it holds the instructions, the retrieved chunks, and the question.
**RAG**: Retrieval-augmented generation. Look up the right pieces of your own documents and give them to the model before it answers. See [what RAG is](lesson:rag/what-is-rag).
**Rank**: Position in a sorted list. Rank 1 is the best match.
**Reranker**: A slower, sharper model that reorders a short list of search results by reading each one with the question.
**Retrieval**: Finding the pieces of text most likely to hold the answer.
**Sandbox**: A box that limits what a program can reach, even if it tries to reach further.
**Semantic search**: Finding text by meaning and not just matching words. Usually done with embeddings.
**Session**: One working run with an agent, from start to finish.
**Step**: One model request plus the tools it calls.
**Sub-agent**: A separate, smaller agent loop started by another agent for one job.
**Token**: A small piece of text, roughly three quarters of a word. Model prices count tokens.
**Tool**: A function a model can ask a harness to run.
**Turn**: One job from your point of view: from your message until the agent stops to wait for you. It may hold many steps.
**Vector**: A list of numbers. An embedding is a vector.
**Vector database**: A database built to find the stored vectors closest to a given one, quickly.
**Vector search**: Finding chunks whose embeddings are closest to the question's embedding.

**API**: A way for one program to ask another to do something, usually over the web.
**Alias (model registry)**: A movable name like "champion" that points at one model version.
**Cross-encoder**: A model that reads a question and one chunk together and scores how well they match. Used for reranking.
**Checkpointer**: Saves a snapshot of an agent's state after each step so it can pause or resume.
**Decode**: The phase where a model writes its answer one token at a time.
**DPO**: Direct preference optimization. Trains a model on pairs of a preferred and a rejected answer.
**Endpointing**: The delay between someone stopping speaking and the system deciding their turn is over.
**Few-shot prompting**: Putting a few input and output examples in the prompt to show the format.
**GGUF**: A single-file format for models that run in llama.cpp.
**Hold-out set**: Examples kept out of training, used to check the model did not just memorize.
**ICE, STUN, TURN**: WebRTC tools for finding a network path between two devices. TURN relays traffic when no direct path works.
**KV cache**: Saved keys and values for earlier tokens, so the model does not recompute them for each new token.
**LoRA**: Fine-tuning that freezes the model and trains small add-on matrices.
**Middleware**: Code that runs before and after each step of an agent loop.
**Prefill**: The phase where a model reads the whole prompt at once.
**QLoRA**: LoRA on a model whose weights are stored in 4 bits to save memory.
**Quantization**: Storing a model's numbers with fewer bits so it is smaller and runs on smaller hardware.
**Reducer**: In LangGraph, the rule for merging a node's update into the state: replace or append.
**SFT**: Supervised fine-tuning. Training on pairs of input and wanted output.
**SIP**: The protocol that starts, changes, and ends phone calls over the internet.
**Thread**: One conversation's chain of saved states in LangGraph.
**Time to first token (TTFT)**: How long a user waits before any output appears.
**Trace**: A step-by-step record of one request: model calls, tool calls, inputs, outputs, time, cost.
**VAD**: Voice activity detection. A small model that tells speech from silence.
**WebRTC**: A way for browsers and apps to send audio and video directly between devices.

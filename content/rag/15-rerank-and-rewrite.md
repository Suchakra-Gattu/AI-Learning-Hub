---
title: Rerank and rewrite, two upgrades to search
summary: Fetch more candidates and let a stricter judge pick the best. Rewrite vague questions so they match your documents.
time: 20 min
---

You have [search that works](lesson:rag/retrieval-that-works). This lesson adds two upgrades used in many production systems. Both come after you have a [test set](lesson:rag/measure-quality). Without one you cannot tell whether they help.

## Upgrade 1: rerank

Fast search is rough. It compares a question to thousands of chunks using a cheap score. A **reranker** is a slower, stricter second look at only the best few.

The pattern:

1. Search fast and fetch a **wide net**, say 20 chunks.
2. Score each chunk against the question with a stronger model.
3. Keep the top 3 to 5 and send those to the prompt.

NVIDIA's write-up gives a worked version of this: fetch 45 candidates fast, rerank, keep the top 5 ([source](https://developer.nvidia.com/blog/enhancing-rag-pipelines-with-re-ranking/)). The LlamaIndex production guide suggests retrieving 10 to 20 and reranking to 3 to 5, with a local **cross-encoder** as a sensible default and a model used as a reranker as the costliest option ([source](https://developers.llamaindex.ai/python/framework/optimizing/production_rag/)).

A **cross-encoder** reads the question and one chunk together and outputs one relevance score. It is more accurate than comparing two stored vectors, but you must run it once per candidate, which is why you only use it on a short list.

| Reranker | Cost | Delay |
|---|---|---|
| Local cross-encoder | Your compute | Grows with candidates |
| Hosted rerank API | Per request | Network round trip |
| Language model as judge | Highest | Highest |

## Upgrade 2: rewrite the question

People type short, vague questions: "tent refund?" Your documents say "Tents can be returned within 60 days." The words barely overlap.

Two common fixes:

- **Query expansion.** A model writes a few alternative versions of the question. You search with each and merge the results. The Haystack cookbook shows this: about four variants, one search each, merge ([source](https://haystack.deepset.ai/cookbook/query-expansion)). Their example went from 3 to 6 documents found.
- **HyDE** (hypothetical document embeddings). The model writes a fake answer first, and you search using the fake answer, which looks more like your documents than the question does. See the [paper](https://arxiv.org/abs/2212.10496). The risk: if the fake answer has wrong details, the search follows them.

## Try it: toy versions, honest results

`code/rag/stage5_advanced.py` has a toy reranker (it counts shared words and word pairs) and a toy expander (a small synonym list). Real output on the 20 sample questions:

```text
20 questions, top 3 chunks each

bm25, no label         top-1  70%   top-3  90%   MRR 0.78
bm25 + context label   top-1  75%   top-3  95%   MRR 0.83
+ rerank (toy)         top-1  75%   top-3  95%   MRR 0.83
+ expansion (toy)      top-1  75%   top-3  95%   MRR 0.83
```

Read this carefully. The toys changed nothing. That is the honest result: this sample has four short files, and plain BM25 already finds most answers. One question is 5 points, so a one-question change is noise. The code shows the **shape** of each upgrade, not the gain you will see on a large, messy collection. On your own data, build the test set first, then try them one at a time and keep the ones that move the numbers.

:::warn Each upgrade has a price
Reranking adds delay and cost per request. Rewriting adds a model call before search even starts. If top-3 recall is already 95%, you may have nothing to gain.
:::

:::check You have a reranker. Why not rerank the whole index?
Rerankers score one chunk at a time with a heavy model. Doing that for every chunk is far too slow and costly. You use fast search to cut the list down first.
:::

Next: [contextual chunks](lesson:rag/contextual-chunks).

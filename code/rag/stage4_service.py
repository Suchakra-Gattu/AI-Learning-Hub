"""Stage 4: wrap the pipeline in a web service with the basics production needs.

Install:  pip install fastapi uvicorn
Run:      uvicorn stage4_service:app --port 8000
Try:      curl -X POST localhost:8000/ask -H "content-type: application/json" -d '{"question":"How long do I have to return a tent?"}'

What this adds over stage 3:
  - an HTTP endpoint with input limits
  - a request id and a timing log line for every call
  - a cache, so the same question does not cost money twice
  - "no good chunks found" -> we refuse without calling the model
  - an error path that does not leak internals
  - /health for the platform to check
"""
import json
import logging
import time
import uuid
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from common import load_documents, build_prompt, ask_llm
from chunking import chunk_all
from retrievers import hybrid_search

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("rag")

CHUNKS = chunk_all(load_documents())  # built once at startup, not per request
MIN_CHUNKS = 1

app = FastAPI(title="Northwind support bot")


class Ask(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@lru_cache(maxsize=512)
def answer_for(question: str):
    """Cached on the exact question text. (Lesson 11 shows smarter caching.)"""
    chunks = hybrid_search(question, CHUNKS, k=3)
    if len(chunks) < MIN_CHUNKS:
        return {"answer": "I don't have that information.", "sources": [], "model_called": False}
    text = ask_llm(build_prompt(question, chunks))
    return {"answer": text, "sources": sorted({c["source"] for c in chunks}), "model_called": True}


@app.post("/ask")
def ask(body: Ask):
    request_id = uuid.uuid4().hex[:8]
    start = time.perf_counter()
    try:
        result = answer_for(body.question.strip())
    except Exception:  # log the details, return a plain message
        log.exception(json.dumps({"request_id": request_id, "event": "error"}))
        raise HTTPException(status_code=502, detail="The answer service had a problem. Please try again.")
    log.info(
        json.dumps(
            {
                "request_id": request_id,
                "event": "answered",
                "ms": round((time.perf_counter() - start) * 1000),
                "model_called": result["model_called"],
                "sources": result["sources"],
                "cache": answer_for.cache_info().hits,
            }
        )
    )
    return {"request_id": request_id, **result}


@app.get("/health")
def health():
    return {"ok": True, "chunks": len(CHUNKS)}

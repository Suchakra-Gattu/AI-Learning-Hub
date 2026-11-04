"""Small helpers shared by every stage. Standard library only.

Read this file once. It is short on purpose.
"""
import json
import os
import re
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def load_documents(folder=DATA_DIR):
    """Read every .md file in a folder. Returns a list of {"source", "text"}."""
    docs = []
    for path in sorted(Path(folder).glob("*.md")):
        docs.append({"source": path.name, "text": path.read_text(encoding="utf-8")})
    return docs


def tokenize(text):
    """Lowercase words. 'Refunds, 5-7 days' -> ['refunds', '5', '7', 'days']."""
    return re.findall(r"[a-z0-9]+", text.lower())


STOPWORDS = set(
    "a an the of to in on for and or is are was were be do does can i my me you your it its "
    "with at by from that this how what when where which who if not no".split()
)


def content_words(text):
    """Words that carry meaning. Drops 'the', 'is', and similar."""
    return [w for w in tokenize(text) if w not in STOPWORDS]


def build_prompt(question, chunks):
    """Put the question and the retrieved text together. This is the 'A' in RAG."""
    context = "\n\n".join(f"[{i + 1}] (source: {c['source']})\n{c['text']}" for i, c in enumerate(chunks))
    return (
        "You answer questions for a store's customers using ONLY the notes below.\n"
        "If the notes do not contain the answer, say: \"I don't have that information.\"\n"
        "After each fact, add the note number in square brackets, like [1].\n\n"
        f"NOTES:\n{context}\n\n"
        f"QUESTION: {question}\n"
        "ANSWER:"
    )


def ask_llm(prompt):
    """Send the prompt to a model if you have an API key. Otherwise show the prompt.

    Uses Anthropic's HTTP API directly so you do not need to install anything.
    Set ANTHROPIC_API_KEY to turn it on. Set LLM_MODEL to change the model.
    """
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return "(No ANTHROPIC_API_KEY set, so no model call. This is the prompt a model would receive.)\n\n" + prompt
    body = json.dumps(
        {
            "model": os.environ.get("LLM_MODEL", "claude-sonnet-5-5"),
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["content"][0]["text"]

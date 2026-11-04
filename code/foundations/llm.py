"""One function that calls a model. Standard library only.

Set ANTHROPIC_API_KEY to use a real model. Without it, ask() returns None
and callers show what they would have sent. Change the model with LLM_MODEL.
"""
import json
import os
import urllib.request


def ask(prompt, system=None, max_tokens=400):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    body = {"model": os.environ.get("LLM_MODEL", "claude-sonnet-5-5"), "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]}
    if system:
        body["system"] = system
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["content"][0]["text"]

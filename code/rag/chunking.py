"""Chunking: cutting documents into pieces that are good to search.

Stage 1 cut on blank lines. That loses context: the paragraph "You can return most
items within 30 days" does not say it is about *returns*. Here every chunk keeps the
document title and section heading with it.
"""
import re


def chunk_by_headings(doc, max_words=120, overlap_words=20):
    """Split a markdown document on '## ' headings, then split long sections by words.

    Each chunk starts with 'Title > Section' so the search can see what it is about.
    """
    text = doc["text"]
    title_match = re.match(r"#\s+(.*)", text)
    title = title_match.group(1).strip() if title_match else doc["source"]
    sections = re.split(r"\n(?=## )", text)
    chunks = []
    for section in sections:
        lines = section.strip().splitlines()
        if not lines:
            continue
        heading = lines[0].lstrip("# ").strip()
        body = " ".join(l.strip() for l in lines[1:] if l.strip())
        if not body:  # the title-only block
            continue
        label = f"{title} > {heading}"
        words = body.split()
        start = 0
        while start < len(words):
            piece = words[start : start + max_words]
            chunks.append({"source": doc["source"], "text": f"{label}\n{' '.join(piece)}"})
            if start + max_words >= len(words):
                break
            start += max_words - overlap_words
    return chunks


def chunk_all(docs, **kwargs):
    out = []
    for d in docs:
        out.extend(chunk_by_headings(d, **kwargs))
    return out

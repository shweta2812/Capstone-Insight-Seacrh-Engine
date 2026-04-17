"""
ingestion.py
Load competitor data from PDFs, web pages, and plain text → chunk → send to RAG engine.
"""

import uuid
import requests
from typing import List, Dict, Any
from io import BytesIO

from pypdf import PdfReader
from bs4 import BeautifulSoup

from rag_engine import add_documents

CHUNK_SIZE    = int(__import__("os").getenv("CHUNK_SIZE",    512))
CHUNK_OVERLAP = int(__import__("os").getenv("CHUNK_OVERLAP",  50))


# ── Text chunker ──────────────────────────────────────────────────────────────
def chunk_text(text: str, source: str, doc_type: str) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks and attach metadata.
    Uses simple word-count splitting (no external tokenizer required).
    """
    words  = text.split()
    chunks = []
    step   = CHUNK_SIZE - CHUNK_OVERLAP
    for i in range(0, len(words), step):
        chunk_words = words[i : i + CHUNK_SIZE]
        if len(chunk_words) < 20:          # skip tiny trailing chunks
            continue
        chunks.append({
            "id":       str(uuid.uuid4()),
            "text":     " ".join(chunk_words),
            "metadata": {
                "source":    source,
                "type":      doc_type,
                "chunk_idx": len(chunks),
            },
        })
    return chunks


# ── PDF ingestion ──────────────────────────────────────────────────────────────
def ingest_pdf(file_bytes: bytes, source_name: str) -> int:
    """Parse a PDF and add its chunks to the vector store."""
    reader = PdfReader(BytesIO(file_bytes))
    full_text = "\n".join(
        page.extract_text() or "" for page in reader.pages
    )
    chunks = chunk_text(full_text, source=source_name, doc_type="pdf")
    add_documents(chunks)
    return len(chunks)


# ── Web-page ingestion ─────────────────────────────────────────────────────────
def ingest_url(url: str, source_name: str = None) -> int:
    """Scrape a URL, strip HTML, and add chunks to the vector store."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; InsightBot/1.0)"}
    resp    = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup      = BeautifulSoup(resp.text, "html.parser")
    # Remove scripts, styles, nav, footer
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text   = soup.get_text(separator=" ", strip=True)
    name   = source_name or url
    chunks = chunk_text(text, source=name, doc_type="web")
    add_documents(chunks)
    return len(chunks)


# ── Plain-text ingestion ───────────────────────────────────────────────────────
def ingest_text(text: str, source_name: str) -> int:
    """Add arbitrary text (e.g. pasted insurance plan details) to the vector store."""
    chunks = chunk_text(text, source=source_name, doc_type="text")
    add_documents(chunks)
    return len(chunks)


# ── Batch helper ──────────────────────────────────────────────────────────────
def ingest_urls_batch(urls: List[str]) -> Dict[str, Any]:
    """Ingest multiple URLs at once. Returns success/failure per URL."""
    results = {}
    for url in urls:
        try:
            n = ingest_url(url)
            results[url] = {"status": "ok", "chunks": n}
        except Exception as e:
            results[url] = {"status": "error", "detail": str(e)}
    return results

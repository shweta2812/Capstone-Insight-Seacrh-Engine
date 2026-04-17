"""
main.py
FastAPI backend for the Blue Shield Competitor Insight Search Engine.
 
Endpoints:
  POST /search          – RAG search query
  POST /ingest/pdf      – Upload a PDF
  POST /ingest/url      – Ingest a web page
  POST /ingest/urls     – Ingest multiple URLs in batch
  POST /ingest/text     – Ingest plain text
  GET  /health          – Health check
  GET  /stats           – Vector store stats
"""
 
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import chromadb
import os
from dotenv import load_dotenv
 
from rag_engine  import search, collection
from ingestion   import ingest_pdf, ingest_url, ingest_text, ingest_urls_batch
 
load_dotenv()
 
app = FastAPI(
    title="Blue Shield Competitor Insight Engine",
    description="RAG-powered competitor intelligence using AWS Bedrock + ChromaDB",
    version="1.0.0",
)
 
# ── CORS (allow Base44 frontend) ───────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://smart-shield-sense.base44.app",
        "http://localhost:3000",   # local dev
        "http://localhost:5173",   # Vite dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
 
# ── Request / Response models ─────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
 
class SearchResponse(BaseModel):
    answer:      str
    sources:     List[str]
    chunks_used: int
 
class IngestURLRequest(BaseModel):
    url:         str
    source_name: Optional[str] = None
 
class IngestURLsBatchRequest(BaseModel):
    urls: List[str]
 
class IngestTextRequest(BaseModel):
    text:        str
    source_name: str
 
 
# ── Endpoints ─────────────────────────────────────────────────────────────────
 
@app.get("/health")
def health():
    return {"status": "ok", "service": "Insight Engine"}
 
 
@app.get("/stats")
def stats():
    """Return how many document chunks are in the vector store."""
    count = collection.count()
    return {"total_chunks": count, "collection": "competitor_insights"}
 
 
@app.post("/search", response_model=SearchResponse)
def search_endpoint(req: SearchRequest):
    """
    Main RAG endpoint.
    Embeds the query, retrieves relevant chunks, generates an answer via Claude.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        result = search(req.query)
        return SearchResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
 
@app.post("/ingest/pdf")
async def ingest_pdf_endpoint(
    file:        UploadFile = File(...),
    source_name: Optional[str] = None,
):
    """Upload a competitor PDF (plan docs, reports, etc.) and ingest it."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    contents = await file.read()
    name     = source_name or file.filename
    try:
        n = ingest_pdf(contents, source_name=name)
        return {"status": "ok", "source": name, "chunks_ingested": n}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
 
@app.post("/ingest/url")
def ingest_url_endpoint(req: IngestURLRequest):
    """Scrape and ingest a single competitor web page."""
    try:
        n = ingest_url(str(req.url), source_name=req.source_name)
        return {"status": "ok", "source": req.url, "chunks_ingested": n}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
 
@app.post("/ingest/urls")
def ingest_urls_endpoint(req: IngestURLsBatchRequest):
    """Ingest multiple URLs at once (e.g. all Anthem plan pages)."""
    results = ingest_urls_batch(req.urls)
    return {"results": results}
 
 
@app.post("/ingest/text")
def ingest_text_endpoint(req: IngestTextRequest):
    """Ingest arbitrary text (pasted plan details, notes, articles)."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    try:
        n = ingest_text(req.text, source_name=req.source_name)
        return {"status": "ok", "source": req.source_name, "chunks_ingested": n}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
 
# ── Run locally ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
 

"""
rag_engine.py
Core RAG logic: embed documents, store in ChromaDB, retrieve + generate answers via AWS Bedrock
"""
 
import os
import json
import boto3
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from typing import List, Dict, Any
 
load_dotenv()
 
# ── AWS Bedrock clients ──────────────────────────────────────────────────────
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-west-2"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
 
LLM_MODEL       = os.getenv("BEDROCK_LLM_MODEL", "anthropic.claude-3-5-sonnet-20241022-v2:0")
EMBEDDING_MODEL = os.getenv("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
TOP_K           = int(os.getenv("TOP_K_RESULTS", 5))
 
# ── ChromaDB setup ────────────────────────────────────────────────────────────
chroma_client = chromadb.PersistentClient(
    path=os.getenv("CHROMA_DB_PATH", "./chroma_db"),
    settings=Settings(anonymized_telemetry=False),
)
collection = chroma_client.get_or_create_collection(
    name="competitor_insights",
    metadata={"hnsw:space": "cosine"},
)
 
 
# ── Embedding ─────────────────────────────────────────────────────────────────
def embed_text(text: str) -> List[float]:
    """Embed a single string using Amazon Titan Embeddings v2 via Bedrock."""
    body = json.dumps({"inputText": text})
    response = bedrock_runtime.invoke_model(
        modelId=EMBEDDING_MODEL,
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    result = json.loads(response["body"].read())
    return result["embedding"]
 
 
# ── Add documents to vector store ─────────────────────────────────────────────
def add_documents(chunks: List[Dict[str, Any]]):
    """
    Add text chunks to ChromaDB.
 
    Each chunk dict should have:
        {
            "id":       "unique-id",
            "text":     "chunk text ...",
            "metadata": {"source": "Anthem 2024 Plan", "type": "pdf", ...}
        }
    """
    if not chunks:
        return
 
    ids        = [c["id"]       for c in chunks]
    texts      = [c["text"]     for c in chunks]
    metadatas  = [c["metadata"] for c in chunks]
    embeddings = [embed_text(t) for t in texts]
 
    collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=embeddings,
    )
    print(f"[RAG] Upserted {len(chunks)} chunks into ChromaDB.")
 
 
# ── Retrieve relevant chunks ───────────────────────────────────────────────────
def retrieve(query: str, top_k: int = TOP_K) -> List[Dict[str, Any]]:
    """Retrieve the top-k most relevant chunks for a query."""
    query_embedding = embed_text(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
 
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text":     doc,
            "metadata": meta,
            "score":    round(1 - dist, 4),   # cosine similarity (higher = better)
        })
    return chunks
 
 
# ── Generate answer with Claude via Bedrock ───────────────────────────────────
def generate_answer(query: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a RAG prompt and call Claude 3.5 Sonnet v2 on AWS Bedrock.
    Returns the answer text plus the source citations used.
    """
    context_text = "\n\n".join(
        f"[Source: {c['metadata'].get('source', 'Unknown')}]\n{c['text']}"
        for c in context_chunks
    )
 
    system_prompt = """You are an expert healthcare insurance analyst helping Blue Shield of California
understand its competitors. You answer questions using only the provided context documents.
If the context does not contain enough information, say so clearly.
Always cite the sources you used by referencing [Source: ...] tags."""
 
    user_message = f"""Context documents:
{context_text}
 
---
Question: {query}
 
Please provide a clear, structured answer based on the context above."""
 
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    })
 
    response = bedrock_runtime.invoke_model(
        modelId=LLM_MODEL,
        contentType="application/json",
        accept="application/json",
        body=body,
    )
 
    result   = json.loads(response["body"].read())
    answer   = result["content"][0]["text"]
    sources  = list({c["metadata"].get("source", "Unknown") for c in context_chunks})
 
    return {"answer": answer, "sources": sources, "chunks_used": len(context_chunks)}
 
 
# ── Full search pipeline ───────────────────────────────────────────────────────
def search(query: str) -> Dict[str, Any]:
    """End-to-end: retrieve relevant chunks then generate an answer."""
    chunks = retrieve(query)
    if not chunks:
        return {
            "answer":       "No relevant documents found. Please ingest some data first.",
            "sources":      [],
            "chunks_used":  0,
        }
    return generate_answer(query, chunks)
 

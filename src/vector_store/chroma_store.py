import chromadb
from sentence_transformers import SentenceTransformer
from config import VECTOR_DB_DIR, EMBEDDING_MODEL, COLLECTION_NAME, TOP_K


_client = None
_collection = None
_model = None


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
    return _client


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_collection():
    global _collection
    if _collection is None:
        _collection = _get_client().get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def index_chunks(chunks: list[dict], batch_size: int = 100) -> None:
    collection = get_collection()
    model = _get_model()
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["text"] for c in batch]
        embeddings = model.encode(texts, show_progress_bar=False).tolist()
        ids = [c["chunk_id"] for c in batch]
        metadatas = [
            {
                "company": c["company"],
                "company_display": c["company_display"],
                "year": str(c.get("year", "")),
                "quarter": c.get("quarter", ""),
                "period": c.get("period", ""),
                "source_type": c.get("source_type", ""),
                "chunk_index": str(c.get("chunk_index", 0)),
                "filename": c.get("filename", ""),
            }
            for c in batch
        ]
        collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        print(f"  Indexed {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")


def semantic_search(query: str, n_results: int = TOP_K, filters: dict = None) -> list[dict]:
    collection = get_collection()
    model = _get_model()
    embedding = model.encode([query]).tolist()
    where = filters if filters else None
    results = collection.query(
        query_embeddings=embedding,
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({"text": doc, "metadata": meta, "score": 1 - dist})
    return hits


def collection_stats() -> dict:
    collection = get_collection()
    count = collection.count()
    return {"total_chunks": count}

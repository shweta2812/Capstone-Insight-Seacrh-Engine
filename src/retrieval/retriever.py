from rank_bm25 import BM25Okapi
from src.vector_store.chroma_store import semantic_search, get_collection
from config import TOP_K

COMPANY_ALIASES = {
    "elevance": "elevance",
    "anthem": "elevance",
    "elevance health": "elevance",
    "united": "united",
    "unitedhealth": "united",
    "unitedhealthcare": "united",
    "unh": "united",
    "optum": "united",
    "aetna": "aetna",
    "cvs": "aetna",
    "cvs health": "aetna",
    "cigna": "cigna",
    "cigna group": "cigna",
    "evernorth": "cigna",
    "humana": "humana",
    "centene": "centene",
    "wellcare": "centene",
    "molina": "molina",
    "molina healthcare": "molina",
    "oscar": "oscar",
    "oscar health": "oscar",
}


def _detect_company(query: str) -> str | None:
    q = query.lower()
    for alias, key in COMPANY_ALIASES.items():
        if alias in q:
            return key
    return None


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def hybrid_search(query: str, n_results: int = TOP_K, filters: dict = None) -> list[dict]:
    # Auto-detect company from query if no filter already set
    if not filters or not filters.get("company"):
        detected = _detect_company(query)
        if detected:
            filters = {**(filters or {}), "company": detected}
    semantic_hits = semantic_search(query, n_results=n_results * 2, filters=filters)
    if not semantic_hits:
        return []

    corpus = [h["text"] for h in semantic_hits]
    bm25 = BM25Okapi([_tokenize(doc) for doc in corpus])
    bm25_scores = bm25.get_scores(_tokenize(query))
    max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0

    for i, hit in enumerate(semantic_hits):
        bm25_norm = bm25_scores[i] / max_bm25
        hit["hybrid_score"] = 0.6 * hit["score"] + 0.4 * bm25_norm

    ranked = sorted(semantic_hits, key=lambda x: x["hybrid_score"], reverse=True)
    return ranked[:n_results]


def get_context_string(hits: list[dict]) -> str:
    parts = []
    for i, hit in enumerate(hits, 1):
        meta = hit["metadata"]
        source = f"{meta.get('company_display', '')} {meta.get('period', '')}"
        parts.append(f"[Source {i}: {source}]\n{hit['text']}")
    return "\n\n---\n\n".join(parts)


def format_citations(hits: list[dict]) -> list[dict]:
    citations = []
    seen = set()
    for i, hit in enumerate(hits, 1):
        meta = hit["metadata"]
        key = f"{meta.get('company')}_{meta.get('period')}"
        citations.append({
            "ref": i,
            "company": meta.get("company_display", ""),
            "period": meta.get("period", ""),
            "source_type": meta.get("source_type", ""),
            "filename": meta.get("filename", ""),
            "score": round(hit.get("hybrid_score", hit.get("score", 0)), 3),
            "snippet": hit["text"][:200] + "...",
        })
    return citations

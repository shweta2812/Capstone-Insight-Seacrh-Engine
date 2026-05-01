"""
Article deduplication: fingerprint hash + semantic similarity.
"""
import hashlib
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

_stats = {"checked": 0, "duplicates_caught": 0, "last_run": None}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def fingerprint(headline: str, body: str) -> str:
    key = _normalize(headline) + _normalize(body[:100])
    return hashlib.sha256(key.encode()).hexdigest()


def load_recent_fingerprints(company: str, days: int = 7) -> tuple[dict[str, str], list[str]]:
    """
    Returns (fingerprint→filename dict, list of recent headlines)
    for news articles saved in the past N days.
    """
    from config import DATA_RAW
    base = DATA_RAW / "news" / company
    if not base.exists():
        return {}, []

    cutoff = datetime.now() - timedelta(days=days)
    fps: dict[str, str] = {}
    headlines: list[str] = []

    for f in base.glob("*.txt"):
        try:
            date_str = f.stem[:10]
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff:
                continue
        except ValueError:
            continue

        text = f.read_text(encoding="utf-8", errors="ignore")
        lines = text.split("\n")
        title = next((l.replace("Title: ", "") for l in lines if l.startswith("Title:")), "")
        blank = next((i for i, l in enumerate(lines) if l == ""), 5)
        body = "\n".join(lines[blank:])

        fp = fingerprint(title, body)
        fps[fp] = f.name
        if title:
            headlines.append(title)

    return fps, headlines


def _cosine_similarity(headline1: str, headline2: str) -> float:
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embs = model.encode([headline1, headline2])
        a, b = embs[0], embs[1]
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
    except Exception as e:
        logger.warning(f"[dedup] Semantic similarity error: {e}")
        return 0.0


def is_duplicate(
    headline: str,
    body: str,
    recent_fingerprints: dict[str, str],
    recent_headlines: list[str],
) -> bool:
    """Return True if the article should be skipped as a near-duplicate."""
    global _stats
    _stats["checked"] += 1

    fp = fingerprint(headline, body)

    if fp in recent_fingerprints:
        logger.info(f"[dedup] Exact match: '{headline[:60]}' → {recent_fingerprints[fp]}")
        _stats["duplicates_caught"] += 1
        return True

    for existing in recent_headlines:
        sim = _cosine_similarity(headline, existing)
        if sim > 0.85:
            logger.info(f"[dedup] Semantic duplicate (sim={sim:.2f}): '{headline[:60]}'")
            _stats["duplicates_caught"] += 1
            return True

    return False


def get_stats() -> dict:
    return {**_stats}


def reset_stats():
    global _stats
    _stats = {"checked": 0, "duplicates_caught": 0, "last_run": datetime.now().isoformat()}

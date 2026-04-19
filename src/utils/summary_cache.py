"""
Persistent cache for AI-generated summaries and insights.
Stored as JSON files in data/summaries/{company}/{slug}.json
"""
import json
import re
from pathlib import Path
from datetime import datetime

CACHE_DIR = Path("data/summaries")


def _slug(text: str) -> str:
    return re.sub(r"[^\w-]", "_", text.lower()).strip("_")


def _cache_path(company: str, doc_key: str) -> Path:
    return CACHE_DIR / company / f"{_slug(doc_key)}.json"


def get_cached(company: str, doc_key: str) -> dict | None:
    path = _cache_path(company, doc_key)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
    return None


def save_cache(company: str, doc_key: str, summary: str, insights: str) -> None:
    path = _cache_path(company, doc_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "summary": summary,
        "insights": insights,
        "generated_at": datetime.now().isoformat(),
    }))

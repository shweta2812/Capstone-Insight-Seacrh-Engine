import json
import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
import re
import threading

from src.ingestion.loader import load_all_transcripts, NEWS_DIR
from src.ingestion.cleaner import clean_text
from src.utils.helpers import TOPIC_KEYWORDS
from src.scraper.sources import SOURCES
from src.utils.summary_cache import get_cached, save_cache
from src.scraper.deduplicator import get_stats as get_dedup_stats
from config import ANTHROPIC_API_KEY, TOPICS_FILE, COMPANIES_CONFIG, BASE_DIR

SUMMARIES_DIR = BASE_DIR / "data" / "summaries" / "topics"

app = FastAPI(title="CI Insights Engine API")

# ── Auto-update state ──────────────────────────────────────────────────────────
_last_update: dict = {"time": None, "new_docs": 0, "new_articles": 0, "status": "pending"}
_update_lock = threading.Lock()


def _run_auto_update():
    global _last_update
    if not _update_lock.acquire(blocking=False):
        return
    try:
        _last_update["status"] = "running"
        from scripts.auto_update import run_update
        result = run_update(summarize=bool(ANTHROPIC_API_KEY))
        _last_update = {
            "time": datetime.now().isoformat(),
            "new_docs": result.get("new_docs", 0),
            "new_articles": result.get("new_articles", 0),
            "status": "ok",
        }
    except Exception as e:
        _last_update["status"] = f"error: {e}"
        print(f"[auto-update] Error: {e}")
    finally:
        _update_lock.release()


@app.on_event("startup")
def startup():
    # Delay heavy background work by 30s so the server is responsive immediately
    def _delayed_start():
        import time
        time.sleep(30)
        _run_auto_update()

    threading.Thread(target=_delayed_start, daemon=True).start()

    scheduler = BackgroundScheduler()
    scheduler.add_job(_run_auto_update, "interval", hours=6, id="auto_update")
    scheduler.start()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ────────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    question: str
    filters: dict = {}
    history: list = []

class InsightsRequest(BaseModel):
    company: str
    year: int
    quarter: str

class TopicCreate(BaseModel):
    topic_name: str
    search_keywords: list[str]

# ── Topics helpers ─────────────────────────────────────────────────────────────

def _load_topics_data() -> dict:
    if not TOPICS_FILE.exists():
        return {"topics": []}
    return json.loads(TOPICS_FILE.read_text(encoding="utf-8"))


def _save_topics_data(data: dict):
    TOPICS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Existing routes ────────────────────────────────────────────────────────────

@app.get("/stats")
def get_stats():
    docs = load_all_transcripts()
    try:
        from src.vector_store.chroma_store import collection_stats
        chunks = collection_stats()["total_chunks"]
    except Exception:
        chunks = 0

    companies = sorted(set(d["company_display"] for d in docs))
    years = sorted(set(d["year"] for d in docs if d["year"]))
    counts = {}
    for d in docs:
        counts[d["company_display"]] = counts.get(d["company_display"], 0) + 1

    return {
        "total_documents": len(docs),
        "total_chunks": chunks,
        "companies": companies,
        "years": years,
        "company_doc_counts": counts,
    }


@app.get("/documents")
def get_documents(company: str = Query(None), year: str = Query(None)):
    docs = load_all_transcripts()
    if company:
        docs = [d for d in docs if d["company_display"] == company]
    if year:
        docs = [d for d in docs if str(d.get("year", "")) == year]
    docs = sorted(docs, key=lambda d: (-(d["year"] or 0), d["quarter"] or ""))
    return [
        {
            "company": d["company"],
            "company_display": d["company_display"],
            "year": d["year"],
            "quarter": d["quarter"],
            "period": d["period"],
            "source_type": d["source_type"],
            "char_count": d["char_count"],
            "filename": d["filename"],
        }
        for d in docs
    ]


@app.get("/documents/preview", response_class=PlainTextResponse)
def preview_document(filename: str = Query(...)):
    docs = load_all_transcripts()
    doc = next((d for d in docs if d["filename"] == filename), None)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc["text"][:5000]


@app.post("/search")
def search(req: SearchRequest):
    try:
        from src.retrieval.retriever import hybrid_search, get_context_string, format_citations
    except ImportError:
        raise HTTPException(503, "Vector DB not initialized. Run ingest script first.")

    filters = {}
    if req.filters.get("company"):
        filters["company"] = req.filters["company"]
    if req.filters.get("year"):
        filters["year"] = int(req.filters["year"]) if str(req.filters["year"]).isdigit() else req.filters["year"]

    hits = hybrid_search(req.question, filters=filters if filters else None)
    context = get_context_string(hits) if hits else ""
    citations = format_citations(hits) if hits else []

    if not ANTHROPIC_API_KEY:
        answer = f"[Demo mode — no ANTHROPIC_API_KEY set]\n\nFound {len(hits)} relevant chunks."
    else:
        from src.llm.claude_client import answer_question
        answer = answer_question(req.question, context, req.history)

    return {"answer": answer, "citations": citations}


@app.post("/insights")
def generate_insights_endpoint(req: InsightsRequest):
    docs = load_all_transcripts()
    co_map = {v["display_name"]: k for k, v in COMPANIES_CONFIG.items()}
    co_key = co_map.get(req.company, req.company.lower().split()[0])
    doc = next(
        (d for d in docs if d["company"] == co_key and d["year"] == req.year and d["quarter"] == req.quarter),
        None,
    )
    if not doc:
        raise HTTPException(404, f"Document not found: {req.company} {req.year} {req.quarter}")

    if not ANTHROPIC_API_KEY:
        insights = (
            f"• [Strategy] {req.company} focused on expanding value-based care partnerships\n"
            f"• [Financial] Premium revenue growth driven by Medicare Advantage enrollment gains\n"
            f"• [Product] New digital health tools launched for chronic disease management\n"
            f"• [Market] Competitive pressure in commercial segment from regional plans\n"
            f"• [Technology] AI-powered prior authorization to reduce administrative burden"
        )
    else:
        from src.llm.claude_client import generate_insights
        insights = generate_insights(doc["text"], req.company, doc["period"])

    return {"insights": insights, "company": req.company, "period": doc["period"]}


def _count_keyword(text: str, keywords: list) -> int:
    text_lower = text.lower()
    return sum(len(re.findall(r'\b' + re.escape(kw.lower()) + r'\b', text_lower)) for kw in keywords)


@app.get("/trends")
def get_trends(topic: str = Query(...), companies: list[str] = Query(default=[])):
    if topic not in TOPIC_KEYWORDS:
        raise HTTPException(400, f"Unknown topic: {topic}")
    docs = load_all_transcripts()
    if companies:
        docs = [d for d in docs if d["company_display"] in companies]
    rows: dict[str, dict] = {}
    for doc in docs:
        period = doc["period"]
        if period not in rows:
            rows[period] = {"period": period, "year": doc["year"], "quarter": doc["quarter"]}
        count = _count_keyword(doc["text"], TOPIC_KEYWORDS[topic])
        rows[period][doc["company_display"]] = count
    return sorted(rows.values(), key=lambda r: (r["year"] or 0, r["quarter"] or ""))


@app.get("/documents/filing")
def get_filing_detail(company: str = Query(...), period: str = Query(...)):
    docs = load_all_transcripts()
    doc = next(
        (d for d in docs if d["company_display"] == company and d["period"] == period
         and d["source_type"] != "news"),
        None,
    )
    if not doc:
        raise HTTPException(404, "Filing not found")
    cached = get_cached(doc["company"], period)
    if not cached and ANTHROPIC_API_KEY:
        from src.llm.claude_client import generate_insights, summarize_document
        summary = summarize_document(doc["text"], company, period)
        insights = generate_insights(doc["text"], company, period)
        save_cache(doc["company"], period, summary, insights)
        cached = {"summary": summary, "insights": insights}
    return {
        "company": company,
        "period": period,
        "source_type": doc["source_type"],
        "filing_date": doc.get("period", ""),
        "char_count": doc["char_count"],
        "filename": doc["filename"],
        "text_preview": doc["text"][:3000],
        "summary": cached.get("summary") if cached else None,
        "insights": cached.get("insights") if cached else None,
    }


@app.get("/news/list")
def get_news_list(company_display: str = Query(...)):
    docs = load_all_transcripts()
    news = [d for d in docs if d["company_display"] == company_display and d["source_type"] == "news"]
    news_sorted = sorted(news, key=lambda d: d["period"], reverse=True)
    result = []
    for d in news_sorted:
        lines = d["text"].split("\n")
        title = next((l.replace("Title: ", "") for l in lines if l.startswith("Title:")), d["filename"])
        url = next((l.replace("URL: ", "") for l in lines if l.startswith("URL:")), "")
        source = next((l.replace("Source: ", "") for l in lines if l.startswith("Source:")), "")
        date = next((l.replace("Date: ", "") for l in lines if l.startswith("Date:")), d["period"])
        cached = get_cached(d["company"], d["filename"])
        result.append({
            "filename": d["filename"],
            "title": title,
            "date": date,
            "url": url,
            "source": source,
            "ai_summary": cached.get("insights") if cached else None,
        })
    return result


@app.post("/news/summarize")
def summarize_news(filename: str = Query(...), company_display: str = Query(...)):
    docs = load_all_transcripts()
    doc = next((d for d in docs if d["filename"] == filename and d["source_type"] == "news"), None)
    if not doc:
        raise HTTPException(404, "News article not found")
    cached = get_cached(doc["company"], filename)
    if cached:
        return cached
    if not ANTHROPIC_API_KEY:
        return {"insights": "[API key required for AI summaries]", "summary": ""}
    lines = doc["text"].split("\n")
    title = next((l.replace("Title: ", "") for l in lines if l.startswith("Title:")), filename)
    from src.llm.claude_client import summarize_news_article
    insights = summarize_news_article(doc["text"], company_display, title)
    save_cache(doc["company"], filename, "", insights)
    return {"insights": insights, "summary": ""}


@app.get("/scraper/status")
def scraper_status():
    docs = load_all_transcripts()
    by_company: dict[str, dict] = {}
    for d in docs:
        co = d["company_display"]
        if co not in by_company:
            by_company[co] = {"filings": [], "news": []}
        if d["source_type"] == "news":
            by_company[co]["news"].append(d["period"])
        else:
            by_company[co]["filings"].append(d["period"])
    return {
        "indexed": {co: v["filings"] for co, v in by_company.items()},
        "news_counts": {co: len(v["news"]) for co, v in by_company.items()},
        "sources": {info["company_display"]: info["ir_url"] for info in SOURCES.values()},
        "last_update": _last_update,
    }


@app.post("/scraper/run")
def run_scraper():
    def _run():
        try:
            from scripts.auto_update import run_update
            run_update(summarize=bool(ANTHROPIC_API_KEY))
        except Exception as e:
            print(f"[scraper] Error: {e}")
    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started", "message": "Scraping in background. Check /stats to see new documents."}


# ── Topics routes ──────────────────────────────────────────────────────────────

@app.get("/topics")
def list_topics():
    return _load_topics_data()


@app.post("/topics")
def create_topic(req: TopicCreate):
    data = _load_topics_data()
    new_topic = {
        "topic_id": str(uuid.uuid4()),
        "topic_name": req.topic_name,
        "search_keywords": req.search_keywords,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_updated": None,
    }
    data.setdefault("topics", []).append(new_topic)
    _save_topics_data(data)

    # Immediately kick off background refresh so data is ready ASAP
    topic_id = new_topic["topic_id"]
    def _run():
        try:
            from scripts.auto_update import run_topic_refresh
            run_topic_refresh(topic_id)
        except Exception as e:
            print(f"[topics] Auto-refresh error for {topic_id}: {e}")
    threading.Thread(target=_run, daemon=True).start()

    return new_topic


@app.delete("/topics/{topic_id}")
def delete_topic(topic_id: str):
    data = _load_topics_data()
    original = data.get("topics", [])
    data["topics"] = [t for t in original if t["topic_id"] != topic_id]
    if len(data["topics"]) == len(original):
        raise HTTPException(404, f"Topic {topic_id} not found")
    _save_topics_data(data)
    return {"deleted": topic_id}


@app.post("/topics/{topic_id}/refresh")
def refresh_topic(topic_id: str):
    def _run():
        from scripts.auto_update import run_topic_refresh
        run_topic_refresh(topic_id)
    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started", "topic_id": topic_id}


@app.get("/topics/{topic_id}/summary")
def get_topic_summary(topic_id: str):
    summaries = {}
    summary_dir = SUMMARIES_DIR / topic_id
    if summary_dir.exists():
        for f in summary_dir.glob("*.json"):
            company_id = f.stem
            summaries[company_id] = json.loads(f.read_text(encoding="utf-8"))
    return {"topic_id": topic_id, "companies": summaries}


# ── Overview route ─────────────────────────────────────────────────────────────

@app.get("/overview")
def get_overview():
    """
    Returns all topics with per-company summaries and source articles.
    Called on dashboard page load.
    """
    data = _load_topics_data()
    topics_out = []

    for topic in data.get("topics", []):
        topic_id = topic["topic_id"]
        companies_out = []

        for company_id, company_cfg in COMPANIES_CONFIG.items():
            cached = _load_topic_summary_file(topic_id, company_id)
            companies_out.append({
                "company_id": company_id,
                "company_name": company_cfg["display_name"],
                "summary": cached.get("summary", "") if cached else "",
                "articles": (cached.get("articles", [])[:3] if cached else []),
                "last_updated": cached.get("generated_at") if cached else None,
                "credibility_tier": _best_tier(cached.get("articles", []) if cached else []),
                "credibility_label": _best_label(cached.get("articles", []) if cached else []),
            })

        topics_out.append({
            "topic_id": topic["topic_id"],
            "topic_name": topic["topic_name"],
            "search_keywords": topic.get("search_keywords", []),
            "last_updated": topic.get("last_updated"),
            "companies": companies_out,
        })

    return {"topics": topics_out, "last_refreshed": _last_update.get("time")}


def _load_topic_summary_file(topic_id: str, company_id: str) -> dict | None:
    path = SUMMARIES_DIR / topic_id / f"{company_id}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _best_tier(articles: list[dict]) -> str:
    if not articles:
        return "0B"
    tiers = [str(a.get("credibility_tier", "0B")) for a in articles]
    for t in ("1", "2", "3", "0B"):
        if t in tiers:
            return t
    return "0B"


def _best_label(articles: list[dict]) -> str:
    tier = _best_tier(articles)
    labels = {"1": "Official source", "2": "Verified press", "3": "General press", "0B": "Unverified"}
    return labels.get(tier, "Unverified")


# ── Dedup stats route ──────────────────────────────────────────────────────────

@app.get("/dedup/stats")
def dedup_stats():
    return get_dedup_stats()

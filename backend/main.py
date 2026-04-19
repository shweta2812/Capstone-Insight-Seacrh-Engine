import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import re
import threading

from src.ingestion.loader import load_all_transcripts, NEWS_DIR
from src.ingestion.cleaner import clean_text
from src.utils.helpers import TOPIC_KEYWORDS
from src.scraper.sources import SOURCES
from src.utils.summary_cache import get_cached, save_cache
from config import ANTHROPIC_API_KEY

app = FastAPI(title="CI Insights Engine API")

# ── Auto-update state ──────────────────────────────────────────────────────────
_last_update: dict = {"time": None, "new_docs": 0, "new_articles": 0, "status": "pending"}
_update_lock = threading.Lock()


def _run_auto_update():
    global _last_update
    if not _update_lock.acquire(blocking=False):
        return  # already running
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
        print(f"[auto-update] Done: {result.get('new_docs',0)} docs, {result.get('new_articles',0)} articles")
    except Exception as e:
        _last_update["status"] = f"error: {e}"
        print(f"[auto-update] Error: {e}")
    finally:
        _update_lock.release()


@app.on_event("startup")
def startup():
    # Run once immediately in background
    threading.Thread(target=_run_auto_update, daemon=True).start()
    # Then every 6 hours
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

# ── Routes ────────────────────────────────────────────────────────────────────

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
        filters["year"] = req.filters["year"]

    hits = hybrid_search(req.question, filters=filters if filters else None)
    if not hits:
        return {"answer": "No relevant documents found. Make sure the vector database is initialized.", "citations": []}

    context = get_context_string(hits)
    citations = format_citations(hits)

    if not ANTHROPIC_API_KEY:
        answer = f"[Demo mode — no ANTHROPIC_API_KEY set]\n\nFound {len(hits)} relevant chunks from: " + \
                 ", ".join(f"{c['company']} {c['period']}" for c in citations[:3])
    else:
        from src.llm.claude_client import answer_question
        answer = answer_question(req.question, context, req.history)

    return {"answer": answer, "citations": citations}


@app.post("/insights")
def generate_insights(req: InsightsRequest):
    docs = load_all_transcripts()
    co_map = {
        "Elevance Health": "elevance",
        "UnitedHealth Group": "united",
        "Aetna (CVS Health)": "aetna",
    }
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

    result = sorted(rows.values(), key=lambda r: (r["year"] or 0, r["quarter"] or ""))
    return result


# ── Document detail & news routes ─────────────────────────────────────────────

@app.get("/documents/filing")
def get_filing_detail(company: str = Query(...), period: str = Query(...)):
    """Return filing text + cached AI insights for a specific company+period."""
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
    """Return all news articles for a company with cached AI summaries."""
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
    """Generate and cache AI summary for a news article on demand."""
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


# ── Scraper routes ─────────────────────────────────────────────────────────────

@app.get("/scraper/status")
def scraper_status():
    """Show what's indexed vs what might be available."""
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
def run_scraper(background_tasks=None):
    """Trigger scrape → index → summarize for all companies."""
    import threading

    def _run():
        try:
            from scripts.auto_update import run_update
            run_update(summarize=bool(ANTHROPIC_API_KEY))
        except Exception as e:
            print(f"[scraper] Error: {e}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return {"status": "started", "message": "Scraping in background. Check /stats to see new documents."}

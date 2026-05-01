"""
Auto-update pipeline: scrape → clean → chunk → index → summarize.
"""
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper.scraper import scrape_all_companies
from src.scraper.news_scraper import scrape_news_all_companies, scrape_topic_for_company, NEWS_COMPANIES
from src.ingestion.loader import load_transcript
from src.ingestion.cleaner import clean_text
from src.chunking.chunker import chunk_document
from src.vector_store.chroma_store import index_chunks, collection_stats
from src.scraper.deduplicator import reset_stats as reset_dedup
from config import ANTHROPIC_API_KEY, TOPICS_FILE, DATA_RAW, BASE_DIR

logger = logging.getLogger("auto_update")


def run_update(summarize: bool = True) -> dict:
    logger.info("=" * 50)
    logger.info("CI Insights Engine — Auto Update")
    logger.info("=" * 50)

    reset_dedup()

    logger.info("--- News Scraper ---")
    news_articles = scrape_news_all_companies()
    logger.info(f"Fetched {len(news_articles)} new news articles.")

    logger.info("--- SEC Filing Scraper ---")
    new_docs = scrape_all_companies()
    if not new_docs and not news_articles:
        logger.info("No new content. Everything is up to date.")
        return {"new_docs": 0, "new_chunks": 0, "summaries": [], "new_articles": 0}

    logger.info(f"Found {len(new_docs)} new transcript(s). Indexing...")

    all_new_chunks = []
    for doc_meta in new_docs:
        doc = load_transcript(Path(doc_meta["filepath"]))
        doc["text"] = clean_text(doc["text"])
        chunks = chunk_document(doc)
        all_new_chunks.extend(chunks)

    for article in news_articles:
        doc = load_transcript(Path(article["filepath"]))
        doc["text"] = clean_text(doc["text"])
        chunks = chunk_document(doc)
        all_new_chunks.extend(chunks)

    if all_new_chunks:
        index_chunks(all_new_chunks)
        stats = collection_stats()
        logger.info(f"Vector DB now has {stats['total_chunks']:,} total chunks.")

    summaries = []
    if summarize and ANTHROPIC_API_KEY:
        from src.llm.claude_client import summarize_document, generate_insights, summarize_news_article
        from src.utils.summary_cache import get_cached, save_cache

        logger.info("Generating AI insights for new SEC filings...")
        for doc_meta in new_docs:
            if get_cached(doc_meta["company"], doc_meta["period"]):
                continue
            doc = load_transcript(Path(doc_meta["filepath"]))
            summary = summarize_document(doc["text"], doc_meta["company_display"], doc_meta["period"])
            insights = generate_insights(doc["text"], doc_meta["company_display"], doc_meta["period"])
            save_cache(doc_meta["company"], doc_meta["period"], summary, insights)
            summaries.append({
                "company": doc_meta["company_display"],
                "period": doc_meta["period"],
                "summary": summary,
                "insights": insights,
            })

        logger.info("Generating AI insights for new news articles...")
        for article in news_articles:
            if get_cached(article["company"], article["filepath"].split("/")[-1]):
                continue
            doc = load_transcript(Path(article["filepath"]))
            lines = doc["text"].split("\n")
            title = next((l.replace("Title: ", "") for l in lines if l.startswith("Title:")), article["filepath"])
            insights = summarize_news_article(doc["text"], article["company_display"], title)
            filename = Path(article["filepath"]).name
            save_cache(article["company"], filename, "", insights)

    return {
        "new_docs": len(new_docs),
        "new_articles": len(news_articles),
        "new_chunks": len(all_new_chunks),
        "summaries": summaries,
    }


def _load_topics() -> list[dict]:
    if not TOPICS_FILE.exists():
        return []
    return json.loads(TOPICS_FILE.read_text(encoding="utf-8")).get("topics", [])


SUMMARIES_DIR = BASE_DIR / "data" / "summaries" / "topics"


def _save_topic_summary(topic_id: str, company_id: str, summary: str, articles: list[dict]):
    out_dir = SUMMARIES_DIR / topic_id
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": summary,
        "articles": articles,
        "generated_at": datetime.now().isoformat(),
    }
    (out_dir / f"{company_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_topic_summary(topic_id: str, company_id: str) -> dict | None:
    path = SUMMARIES_DIR / topic_id / f"{company_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def run_topic_refresh(topic_id: str) -> dict:
    """
    Refresh news and AI summaries for a single topic across all companies in parallel.
    Uses Claude web_search_20250305 as primary source; falls back to cached RSS articles.
    Returns {topic_id, companies_refreshed, articles_found}.
    """
    import anthropic
    from src.scraper.web_search_scraper import search_topic_for_company
    from config import COMPANIES_CONFIG

    topics = _load_topics()
    topic = next((t for t in topics if t["topic_id"] == topic_id), None)
    if not topic:
        logger.error(f"[topic] Topic not found: {topic_id}")
        return {"error": f"Topic {topic_id} not found"}

    logger.info(f"[topic] Refreshing: {topic['topic_name']} (parallel across {len(COMPANIES_CONFIG)} companies)")
    keywords = topic["search_keywords"]

    def _process_company(args: tuple[str, dict]) -> tuple[str, int]:
        """Returns (company_id, article_count). Saves summary file as side effect."""
        company_id, company_cfg = args
        company_display = company_cfg["display_name"]

        # ── Step 1: Claude web_search (primary) ──────────────────────────────
        web_articles: list[dict] = []
        if ANTHROPIC_API_KEY:
            try:
                web_articles = search_topic_for_company(
                    company_name=company_display,
                    topic_name=topic["topic_name"],
                    keywords=keywords,
                    min_articles=2,
                )
                logger.info(f"[topic] {company_display}: {len(web_articles)} web articles")
            except Exception as e:
                logger.error(f"[topic] web_search failed for {company_id}: {e}")

        # ── Step 2: Cached RSS news files (fallback / supplement) ────────────
        news_dir = DATA_RAW / "news" / company_id
        rss_articles: list[dict] = []
        if news_dir.exists():
            for f in sorted(news_dir.glob("*.txt"), reverse=True)[:40]:
                text = f.read_text(encoding="utf-8", errors="ignore")
                lines = text.split("\n")

                tier_raw = next(
                    (l.replace("Credibility-Tier: ", "") for l in lines if l.startswith("Credibility-Tier:")),
                    None,
                )
                tier = tier_raw.strip() if tier_raw else "3"
                if tier == "0A":
                    continue

                if not any(kw.lower() in text.lower() for kw in keywords):
                    continue

                title = next((l.replace("Title: ", "") for l in lines if l.startswith("Title:")), "")
                url = next((l.replace("URL: ", "") for l in lines if l.startswith("URL:")), "")
                date = next((l.replace("Date: ", "") for l in lines if l.startswith("Date:")), "")
                score_raw = next((l.replace("Credibility-Score: ", "") for l in lines if l.startswith("Credibility-Score:")), "0.5")
                label = next((l.replace("Credibility-Label: ", "") for l in lines if l.startswith("Credibility-Label:")), "General press")
                domain = next((l.replace("Source-Domain: ", "") for l in lines if l.startswith("Source-Domain:")), "")

                if not title or not url:
                    continue
                try:
                    score = float(score_raw)
                except ValueError:
                    score = 0.5

                rss_articles.append({
                    "title": title, "url": url, "date": date,
                    "credibility_score": score, "credibility_tier": tier,
                    "credibility_label": label, "source_domain": domain, "summary": "",
                })

        # ── Step 3: Merge & deduplicate, keep top 5 ─────────────────────────
        seen_urls: set[str] = set()
        merged: list[dict] = []
        for a in web_articles + rss_articles:
            if a.get("url") and a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                merged.append(a)

        top5 = sorted(merged, key=lambda a: (a.get("credibility_score", 0), a.get("date", "")), reverse=True)[:5]

        # ── Step 4: AI summary ───────────────────────────────────────────────
        existing = _load_topic_summary(topic_id, company_id)

        if ANTHROPIC_API_KEY and top5:
            try:
                client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                snippets = "\n\n".join(
                    f"[{a.get('date', '')}] {a['title']}\n{a.get('summary', '')}" for a in top5
                )
                msg = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=400,
                    messages=[{"role": "user", "content": (
                        f"You are a competitive intelligence analyst for Blue Shield of California. "
                        f"Analyze the following recent articles about {company_display} related to "
                        f"'{topic['topic_name']}'. Write 4-6 sentences covering: key developments, "
                        f"strategic direction, and implications for Blue Shield of California. "
                        f"Be specific and factual.\n\n{snippets}"
                    )}],
                )
                summary_text = msg.content[0].text
            except Exception as e:
                logger.error(f"[topic] AI summary failed for {company_id}: {e}")
                summary_text = existing.get("summary", "") if existing else ""
        elif not top5:
            if existing and existing.get("summary") and existing["summary"] != f"No recent articles found for {topic['topic_name']}.":
                logger.info(f"[topic] {company_display}: no new articles, keeping existing summary")
                return (company_id, 0)
            summary_text = f"No recent articles found for {topic['topic_name']}."
        else:
            summary_text = f"[API key required] Found {len(top5)} articles."

        _save_topic_summary(topic_id, company_id, summary_text, top5)
        logger.info(f"[topic] {company_display} — {len(top5)} articles saved")
        return (company_id, len(top5))

    # ── Run all companies in parallel (up to 5 threads to avoid API rate limits) ──
    results: list[tuple[str, int]] = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(_process_company, item): item[0] for item in COMPANIES_CONFIG.items()}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                logger.error(f"[topic] Company task failed: {e}")

    companies_refreshed = [r[0] for r in results]
    total_articles = sum(r[1] for r in results)

    # Update last_updated in topics.json
    if TOPICS_FILE.exists():
        data = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
        for t in data.get("topics", []):
            if t["topic_id"] == topic_id:
                t["last_updated"] = datetime.now().isoformat()
        TOPICS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info(f"[topic] Done: {len(companies_refreshed)} companies, {total_articles} articles total")
    return {
        "topic_id": topic_id,
        "companies_refreshed": len(companies_refreshed),
        "articles_found": total_articles,
    }


if __name__ == "__main__":
    result = run_update()
    print(f"\nDone. Added {result['new_docs']} SEC docs, {result['new_articles']} news articles, {result['new_chunks']} chunks.")

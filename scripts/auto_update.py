"""
Auto-update pipeline: scrape new transcripts → clean → chunk → index → summarize.
Run once manually, or schedule via cron / background thread.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper.scraper import scrape_all_companies
from src.scraper.news_scraper import scrape_news_all_companies
from src.ingestion.loader import load_transcript
from src.ingestion.cleaner import clean_text
from src.chunking.chunker import chunk_document
from src.vector_store.chroma_store import index_chunks, collection_stats
from config import ANTHROPIC_API_KEY


def run_update(summarize: bool = True) -> dict:
    print("=" * 50)
    print("CI Insights Engine — Auto Update")
    print("=" * 50)

    # 1a. Scrape news articles (RSS + IR)
    print("\n--- News Scraper ---")
    news_articles = scrape_news_all_companies()
    print(f"Fetched {len(news_articles)} new news articles.")

    # 1b. Scrape new SEC filings / transcripts
    print("\n--- SEC Filing Scraper ---")
    new_docs = scrape_all_companies()
    if not new_docs and not news_articles:
        print("\nNo new content found. Everything is up to date.")
        return {"new_docs": 0, "new_chunks": 0, "summaries": [], "new_articles": 0}

    print(f"\nFound {len(new_docs)} new transcript(s). Indexing...")

    # 2. Load, clean, chunk, index (SEC filings + news articles)
    all_new_chunks = []
    for doc_meta in new_docs:
        doc = load_transcript(Path(doc_meta["filepath"]))
        doc["text"] = clean_text(doc["text"])
        chunks = chunk_document(doc)
        all_new_chunks.extend(chunks)

    # Index news articles as documents too
    for article in news_articles:
        doc = load_transcript(Path(article["filepath"]))
        doc["text"] = clean_text(doc["text"])
        chunks = chunk_document(doc)
        all_new_chunks.extend(chunks)

    if all_new_chunks:
        index_chunks(all_new_chunks)
        stats = collection_stats()
        print(f"Vector DB now has {stats['total_chunks']:,} total chunks.")

    # 3. Auto-generate summaries if API key present
    summaries = []
    if summarize and ANTHROPIC_API_KEY:
        from src.llm.claude_client import summarize_document, generate_insights, summarize_news_article
        from src.utils.summary_cache import get_cached, save_cache

        print("\nGenerating AI insights for new SEC filings...")
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
            print(f"  [ai] Cached insights: {doc_meta['company_display']} {doc_meta['period']}")

        print("\nGenerating AI insights for new news articles...")
        for article in news_articles:
            if get_cached(article["company"], article["filepath"].split("/")[-1]):
                continue
            doc = load_transcript(Path(article["filepath"]))
            lines = doc["text"].split("\n")
            title = next((l.replace("Title: ", "") for l in lines if l.startswith("Title:")), article["filepath"])
            insights = summarize_news_article(doc["text"], article["company_display"], title)
            filename = Path(article["filepath"]).name
            save_cache(article["company"], filename, "", insights)
            print(f"  [ai] Cached news insights: {article['company_display']} — {title[:50]}")

    return {
        "new_docs": len(new_docs),
        "new_articles": len(news_articles),
        "new_chunks": len(all_new_chunks),
        "summaries": summaries,
    }


if __name__ == "__main__":
    result = run_update()
    print(f"\nDone. Added {result['new_docs']} SEC docs, {result['new_articles']} news articles, {result['new_chunks']} chunks.")

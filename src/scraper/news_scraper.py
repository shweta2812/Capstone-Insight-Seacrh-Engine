"""
News scraper: RSS feeds (Google News) + company IR press release pages.
No API key required.
"""
import time
import re
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pathlib import Path
from config import TRANSCRIPTS_DIR

HEADERS = {"User-Agent": "ci-research@blueshield.com"}

# Google News RSS — free, no key, filterable by company name
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

NEWS_COMPANIES = {
    "elevance": {
        "company_display": "Elevance Health",
        "queries": ["Elevance Health earnings", "Anthem Blue Cross earnings"],
        "ir_rss": "https://ir.elevancehealth.com/rss/news-releases.xml",
    },
    "united": {
        "company_display": "UnitedHealth Group",
        "queries": ["UnitedHealth Group earnings", "UnitedHealthcare quarterly results"],
        "ir_rss": None,
    },
    "aetna": {
        "company_display": "Aetna (CVS Health)",
        "queries": ["CVS Health earnings", "Aetna quarterly results"],
        "ir_rss": "https://investors.cvshealth.com/rss/news-releases.xml",
    },
    "cigna": {
        "company_display": "Cigna Group",
        "queries": ["Cigna Group earnings", "Evernorth quarterly results"],
        "ir_rss": None,
    },
    "humana": {
        "company_display": "Humana",
        "queries": ["Humana earnings", "Humana Medicare Advantage quarterly"],
        "ir_rss": None,
    },
    "centene": {
        "company_display": "Centene",
        "queries": ["Centene earnings", "Centene Medicaid quarterly results"],
        "ir_rss": None,
    },
    "molina": {
        "company_display": "Molina Healthcare",
        "queries": ["Molina Healthcare earnings", "Molina quarterly results"],
        "ir_rss": None,
    },
    "oscar": {
        "company_display": "Oscar Health",
        "queries": ["Oscar Health earnings", "Oscar Health quarterly results"],
        "ir_rss": None,
    },
}

NEWS_DIR = Path("data/raw/news")


def _parse_date(entry) -> str:
    """Extract ISO date string from a feedparser entry."""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                pass
    return datetime.now().strftime("%Y-%m-%d")


def _clean_html(html_text: str) -> str:
    soup = BeautifulSoup(html_text or "", "html.parser")
    return soup.get_text(separator=" ").strip()


def _existing_news_ids(company: str) -> set:
    company_dir = NEWS_DIR / company
    if not company_dir.exists():
        return set()
    ids = set()
    for f in company_dir.glob("*.txt"):
        ids.add(f.stem)
    return ids


def _slug(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s-]+", "-", text).strip("-")[:80]


def _save_article(company: str, company_display: str, title: str, date: str,
                  url: str, summary: str, source: str) -> dict | None:
    company_dir = NEWS_DIR / company
    company_dir.mkdir(parents=True, exist_ok=True)

    file_id = f"{date}_{_slug(title)}"
    existing = _existing_news_ids(company)
    if file_id in existing:
        return None

    content = f"Source: {source}\nDate: {date}\nTitle: {title}\nURL: {url}\n\n{summary}"
    filepath = company_dir / f"{file_id}.txt"
    filepath.write_text(content, encoding="utf-8")
    return {
        "company": company,
        "company_display": company_display,
        "date": date,
        "title": title,
        "url": url,
        "source": source,
        "filepath": str(filepath),
    }


def scrape_google_news(company: str, max_per_query: int = 10) -> list[dict]:
    """Scrape Google News RSS for a company."""
    info = NEWS_COMPANIES[company]
    saved = []

    for query in info["queries"]:
        url = GOOGLE_NEWS_RSS.format(query=requests.utils.quote(query))
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"  [news] RSS parse error for '{query}': {e}")
            continue

        for entry in feed.entries[:max_per_query]:
            title = _clean_html(entry.get("title", ""))
            summary = _clean_html(entry.get("summary", entry.get("description", "")))
            link = entry.get("link", "")
            date = _parse_date(entry)

            result = _save_article(
                company, info["company_display"], title, date, link, summary,
                source="Google News RSS"
            )
            if result:
                print(f"  [news] Saved: {info['company_display']} — {title[:60]}")
                saved.append(result)

        time.sleep(0.5)

    return saved


def scrape_ir_rss(company: str) -> list[dict]:
    """Scrape company IR RSS feed if available."""
    info = NEWS_COMPANIES[company]
    if not info.get("ir_rss"):
        return []

    saved = []
    try:
        feed = feedparser.parse(info["ir_rss"])
    except Exception as e:
        print(f"  [news] IR RSS error for {company}: {e}")
        return []

    for entry in feed.entries[:20]:
        title = _clean_html(entry.get("title", ""))
        summary = _clean_html(entry.get("summary", entry.get("description", "")))
        link = entry.get("link", "")
        date = _parse_date(entry)

        result = _save_article(
            company, info["company_display"], title, date, link, summary,
            source=f"{info['company_display']} IR"
        )
        if result:
            print(f"  [news] Saved IR: {info['company_display']} — {title[:60]}")
            saved.append(result)

    time.sleep(0.3)
    return saved


def scrape_news_all_companies() -> list[dict]:
    """Scrape news for all companies. Returns list of newly saved articles."""
    all_new = []
    for company in NEWS_COMPANIES:
        print(f"\nFetching news: {NEWS_COMPANIES[company]['company_display']}...")
        new = scrape_google_news(company)
        new += scrape_ir_rss(company)
        all_new.extend(new)
        print(f"  → {len(new)} new articles")
    return all_new


if __name__ == "__main__":
    results = scrape_news_all_companies()
    print(f"\nTotal new articles saved: {len(results)}")

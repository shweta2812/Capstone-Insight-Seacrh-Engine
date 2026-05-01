"""
News scraper: RSS feeds (Google News) + company IR press release pages.
No API key required.
"""
import logging
import time
import re
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pathlib import Path

from config import COMPANIES_CONFIG, DATA_RAW, LOGS_DIR
from src.scraper.credibility_filter import score_article
from src.scraper.deduplicator import load_recent_fingerprints, is_duplicate, fingerprint

# ── Logging setup (absolute path so it works from any CWD) ────────────────────
_log_file = LOGS_DIR / "scraper.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(_log_file), encoding="utf-8"),
    ],
)
logger = logging.getLogger("news_scraper")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; InsightEngine/1.0)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

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
    "kaiser": {
        "company_display": "Kaiser Permanente",
        "queries": ["Kaiser Permanente health insurance", "Kaiser Permanente news"],
        "ir_rss": None,
    },
    "bluecross_ca": {
        "company_display": "Blue Cross (Anthem CA)",
        "queries": ["Anthem Blue Cross California health insurance", "Anthem California news"],
        "ir_rss": None,
    },
}

NEWS_DIR = DATA_RAW / "news"

# Failed sources log — cleared each run
_failed_sources: list[dict] = []


def get_failed_sources() -> list[dict]:
    return list(_failed_sources)


def _clear_failed_sources():
    global _failed_sources
    _failed_sources = []


def _log_failure(company: str, url: str, reason: str):
    entry = {"company": company, "url": url, "reason": reason,
             "timestamp": datetime.now().isoformat()}
    _failed_sources.append(entry)
    logger.error(f"[{company}] FAILED {url}: {reason}")


def _parse_date(entry) -> str:
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
    return {f.stem for f in company_dir.glob("*.txt")}


def _slug(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s-]+", "-", text).strip("-")[:80]


def _fetch_with_retry(url: str, max_retries: int = 3) -> requests.Response | None:
    """GET with exponential backoff. Returns None on all failures."""
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            wait = 2 ** attempt
            if attempt < max_retries - 1:
                logger.warning(f"Retry {attempt + 1}/{max_retries} for {url}: {e}. Waiting {wait}s")
                time.sleep(wait)
            else:
                return None
    return None


def _save_article(
    company: str, company_display: str, title: str, date: str,
    url: str, summary: str, source: str,
    credibility: dict,
) -> dict | None:
    # Skip Tier 0-A (rejected)
    if credibility["credibility_tier"] == "0A":
        logger.info(f"[{company}] Rejected (Tier 0-A): {title[:60]}")
        return None

    company_dir = NEWS_DIR / company
    company_dir.mkdir(parents=True, exist_ok=True)

    file_id = f"{date}_{_slug(title)}"
    existing_ids = _existing_news_ids(company)
    if file_id in existing_ids:
        return None

    # Deduplication check
    recent_fps, recent_headlines = load_recent_fingerprints(company)
    body_fp = fingerprint(title, summary)
    if is_duplicate(title, summary, recent_fps, recent_headlines):
        logger.info(f"[{company}] Duplicate skipped: {title[:60]}")
        return None

    unverified_flag = "yes" if credibility["credibility_tier"] == "0B" else "no"

    content = (
        f"Source: {source}\n"
        f"Date: {date}\n"
        f"Title: {title}\n"
        f"URL: {url}\n"
        f"Credibility-Score: {credibility['credibility_score']}\n"
        f"Credibility-Tier: {credibility['credibility_tier']}\n"
        f"Credibility-Label: {credibility['credibility_label']}\n"
        f"Source-Domain: {credibility['source_domain']}\n"
        f"Unverified: {unverified_flag}\n"
        f"\n{summary}"
    )
    filepath = company_dir / f"{file_id}.txt"
    filepath.write_text(content, encoding="utf-8")

    logger.info(
        f"[{company}] Saved [{credibility['credibility_label']}]: {title[:60]}"
    )
    return {
        "company": company,
        "company_display": company_display,
        "date": date,
        "title": title,
        "url": url,
        "source": source,
        "filepath": str(filepath),
        **credibility,
    }


def scrape_google_news(company: str, max_per_query: int = 10) -> list[dict]:
    info = NEWS_COMPANIES[company]
    saved = []

    for query in info["queries"]:
        url = GOOGLE_NEWS_RSS.format(query=requests.utils.quote(query))
        try:
            # feedparser handles HTTP internally; use requests for retry
            resp = _fetch_with_retry(url)
            if resp is None:
                _log_failure(company, url, "Max retries exceeded")
                continue
            feed = feedparser.parse(resp.content)
        except Exception as e:
            _log_failure(company, url, str(e))
            continue

        if not feed.entries:
            logger.warning(f"[{company}] No entries for query: {query}")

        for entry in feed.entries[:max_per_query]:
            title = _clean_html(entry.get("title", ""))
            summary = _clean_html(entry.get("summary", entry.get("description", "")))
            link = entry.get("link", "")
            date = _parse_date(entry)
            source_name = getattr(getattr(entry, "source", None), "title", "") or ""

            cred = score_article(link, title=title, source_name=source_name)
            result = _save_article(
                company, info["company_display"], title, date, link, summary,
                source="Google News RSS", credibility=cred,
            )
            if result:
                saved.append(result)

        time.sleep(0.5)

    return saved


def scrape_ir_rss(company: str) -> list[dict]:
    info = NEWS_COMPANIES[company]
    if not info.get("ir_rss"):
        return []

    saved = []
    url = info["ir_rss"]
    try:
        resp = _fetch_with_retry(url)
        if resp is None:
            _log_failure(company, url, "Max retries exceeded")
            return []
        feed = feedparser.parse(resp.content)
    except Exception as e:
        _log_failure(company, url, str(e))
        return []

    for entry in feed.entries[:20]:
        title = _clean_html(entry.get("title", ""))
        summary = _clean_html(entry.get("summary", entry.get("description", "")))
        link = entry.get("link", "")
        date = _parse_date(entry)

        cred = score_article(link, title=title, source_name=info["company_display"])
        result = _save_article(
            company, info["company_display"], title, date, link, summary,
            source=f"{info['company_display']} IR", credibility=cred,
        )
        if result:
            saved.append(result)

    time.sleep(0.3)
    return saved


def scrape_topic_for_company(company: str, keywords: list[str], max_per_keyword: int = 5) -> list[dict]:
    """Search Google News for specific topic keywords for a single company."""
    info = NEWS_COMPANIES.get(company)
    if not info:
        return []

    company_display = info["company_display"]
    saved = []

    for kw in keywords:
        query = f"{company_display} {kw}"
        url = GOOGLE_NEWS_RSS.format(query=requests.utils.quote(query))
        try:
            resp = _fetch_with_retry(url)
            if resp is None:
                _log_failure(company, url, f"Topic query failed: {kw}")
                continue
            feed = feedparser.parse(resp.content)
        except Exception as e:
            _log_failure(company, url, str(e))
            continue

        for entry in feed.entries[:max_per_keyword]:
            title = _clean_html(entry.get("title", ""))
            summary = _clean_html(entry.get("summary", entry.get("description", "")))
            link = entry.get("link", "")
            date = _parse_date(entry)
            source_name = getattr(getattr(entry, "source", None), "title", "") or ""

            cred = score_article(link, title=title, source_name=source_name)
            result = _save_article(
                company, company_display, title, date, link, summary,
                source="Google News RSS (topic)", credibility=cred,
            )
            if result:
                saved.append(result)

        time.sleep(0.5)

    return saved


def scrape_news_all_companies() -> list[dict]:
    _clear_failed_sources()
    all_new = []
    for company in NEWS_COMPANIES:
        logger.info(f"Fetching news: {NEWS_COMPANIES[company]['company_display']}")
        new = scrape_google_news(company)
        new += scrape_ir_rss(company)
        all_new.extend(new)
        logger.info(f"[{company}] {len(new)} new articles")
    if _failed_sources:
        logger.warning(f"Failed sources this run: {len(_failed_sources)}")
    return all_new


if __name__ == "__main__":
    results = scrape_news_all_companies()
    print(f"\nTotal new articles: {len(results)}")
    if _failed_sources:
        print(f"Failed sources ({len(_failed_sources)}):")
        for f in _failed_sources:
            print(f"  {f['company']} — {f['url']}: {f['reason']}")

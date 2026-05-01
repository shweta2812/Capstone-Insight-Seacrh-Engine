"""
Claude-powered web search scraper.
Uses Anthropic API web_search tool to find real-time articles for any topic.
Falls back: 24h → 1 week → 3 months if fewer than min_articles found.
"""
import json
import logging
import re
from datetime import datetime

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from src.scraper.credibility_filter import score_article

logger = logging.getLogger("web_search_scraper")

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


# Time window labels for the search prompt
_TIME_WINDOWS = [
    ("24 hours", "past 24 hours"),
    ("1 week",   "past week"),
    ("3 months", "past 3 months"),
]


def _build_prompt(company_name: str, topic_name: str, keywords: list[str], time_label: str) -> str:
    kw_str = ", ".join(keywords[:5])
    return (
        f"Search for news about **{company_name}** related to **{topic_name}** "
        f"published in the **{time_label}**. "
        f"Keywords to focus on: {kw_str}.\n\n"
        f"Return a JSON array (no markdown fences) of up to 5 articles, each with:\n"
        f"- title: article headline\n"
        f"- url: direct URL to the article\n"
        f"- date: publication date (YYYY-MM-DD)\n"
        f"- source: publication name\n"
        f"- summary: 2–3 sentence summary of the key points relevant to {topic_name}\n\n"
        f"Only include articles that are directly relevant to {company_name} and {topic_name}. "
        f"If fewer than 3 relevant articles exist in this time window, return what you found "
        f"(even 0 is fine — do not fabricate)."
    )


def _parse_articles(text: str) -> list[dict]:
    """Extract JSON array from Claude's response text."""
    # Strip markdown fences if present
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    # Find the first [ ... ] block
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        items = json.loads(match.group())
        return [a for a in items if isinstance(a, dict) and a.get("url")]
    except json.JSONDecodeError:
        return []


def search_topic_for_company(
    company_name: str,
    topic_name: str,
    keywords: list[str],
    min_articles: int = 2,
) -> list[dict]:
    """
    Use Claude web_search to find recent articles about company+topic.
    Falls back to wider time windows if min_articles not found.
    Returns list of article dicts with credibility scores.
    """
    if not ANTHROPIC_API_KEY:
        logger.warning("No ANTHROPIC_API_KEY — skipping web search")
        return []

    client = _get_client()
    articles: list[dict] = []

    for window_name, window_label in _TIME_WINDOWS:
        if len(articles) >= min_articles:
            break

        prompt = _build_prompt(company_name, topic_name, keywords, window_label)
        logger.info(f"[web_search] {company_name} / {topic_name} ({window_label})")

        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2048,
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 5,
                }],
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            logger.error(f"[web_search] API error for {company_name}: {e}")
            break

        # Collect text from all content blocks
        full_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                full_text += block.text

        found = _parse_articles(full_text)
        logger.info(f"[web_search] Found {len(found)} articles in {window_label}")

        for art in found:
            url = art.get("url", "")
            title = art.get("title", "")
            cred = score_article(url, title=title, source_name=art.get("source", ""))

            # Skip Tier 0-A (social media / content farms)
            if cred["credibility_tier"] == "0A":
                continue

            articles.append({
                "title": title,
                "url": url,
                "date": art.get("date", datetime.now().strftime("%Y-%m-%d")),
                "source": art.get("source", ""),
                "summary": art.get("summary", ""),
                "credibility_score": cred["credibility_score"],
                "credibility_tier": cred["credibility_tier"],
                "credibility_label": cred["credibility_label"],
                "source_domain": cred["source_domain"],
                "time_window": window_name,
            })

    # Deduplicate by URL
    seen_urls: set[str] = set()
    unique: list[dict] = []
    for a in articles:
        if a["url"] not in seen_urls:
            seen_urls.add(a["url"])
            unique.append(a)

    return unique


def search_topic_all_companies(
    companies: dict,  # {company_id: display_name}
    topic_name: str,
    keywords: list[str],
) -> dict[str, list[dict]]:
    """Run web search for all companies. Returns {company_id: [articles]}."""
    results: dict[str, list[dict]] = {}
    for company_id, company_name in companies.items():
        results[company_id] = search_topic_for_company(company_name, topic_name, keywords)
    return results

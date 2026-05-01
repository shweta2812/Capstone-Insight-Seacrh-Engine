"""
Credibility scoring for scraped articles.

Tier 1  — Official source  (score 1.0): company IR pages, SEC
Tier 2  — Verified press   (score 0.8): healthcare/finance trade press
Tier 3  — General press    (score 0.5): major general-audience outlets
Tier 0-B — Unverified      (score 0.3): unknown domains; stored but hidden
Tier 0-A — Rejected        (score 0.0): social media, content farms; discarded
"""
import re
from urllib.parse import urlparse

TIER1_DOMAINS = {
    "kaiserpermanente.org", "elevancehealth.com", "uhc.com", "unitedhealthgroup.com",
    "cigna.com", "humana.com", "centene.com", "molinahealthcare.com", "hioscar.com",
    "anthem.com", "aetna.com", "cvs.com", "sec.gov",
    "ir.elevancehealth.com", "investors.cvshealth.com",
    "ir.humana.com", "ir.cigna.com", "ir.centene.com", "ir.molinahealthcare.com",
}

TIER2_DOMAINS = {
    "reuters.com", "apnews.com", "wsj.com", "bloomberg.com",
    "modernhealthcare.com", "fiercehealthcare.com", "healthcarefinancenews.com",
    "beckershospitalreview.com", "beckersspine.com", "statnews.com", "healthaffairs.org",
}

TIER3_DOMAINS = {
    "nytimes.com", "washingtonpost.com", "usatoday.com", "forbes.com",
    "cnbc.com", "businessinsider.com",
}

TIER0A_DOMAINS = {
    "twitter.com", "x.com", "facebook.com", "reddit.com",
    "linkedin.com", "tiktok.com", "instagram.com", "youtube.com",
}

_FARM_DOMAIN_RE = re.compile(r"news247|dailybuzz|viralstories|clickbait|newsburst|viral247", re.I)
_FARM_TITLE_RE  = re.compile(r"click here|you won't believe|shocking reveal", re.I)


def _extract_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host.removeprefix("www.")
    except Exception:
        return ""


def _domain_in(domain: str, tier_set: set) -> bool:
    return domain in tier_set or any(domain.endswith("." + d) for d in tier_set)


def _google_news_score(source_name: str) -> dict | None:
    """Try to score a Google News article by its publisher name."""
    sn = source_name.lower()
    for d in TIER1_DOMAINS:
        base = d.split(".")[0]
        if base in sn or sn in d:
            return {"credibility_score": 1.0, "credibility_tier": "1",
                    "credibility_label": "Official source", "source_domain": source_name}
    for d in TIER2_DOMAINS:
        base = d.split(".")[0]
        if base in sn or sn in d:
            return {"credibility_score": 0.8, "credibility_tier": "2",
                    "credibility_label": "Verified press", "source_domain": source_name}
    for d in TIER3_DOMAINS:
        base = d.split(".")[0]
        if base in sn or sn in d:
            return {"credibility_score": 0.5, "credibility_tier": "3",
                    "credibility_label": "General press", "source_domain": source_name}
    return None


def score_article(url: str, title: str = "", source_name: str = "") -> dict:
    """
    Score an article by credibility.
    Returns: {credibility_score, credibility_tier, credibility_label, source_domain}
    """
    domain = _extract_domain(url)

    # Google News redirect — score by publisher name
    if "news.google.com" in domain:
        if source_name:
            result = _google_news_score(source_name)
            if result:
                return result
        # Unknown Google News source → Tier 3 (still curated by Google)
        return {"credibility_score": 0.5, "credibility_tier": "3",
                "credibility_label": "General press",
                "source_domain": source_name or "news.google.com"}

    # Tier 0-A: Social media
    if _domain_in(domain, TIER0A_DOMAINS):
        return {"credibility_score": 0.0, "credibility_tier": "0A",
                "credibility_label": "Rejected", "source_domain": domain}

    # Tier 0-A: Content farm — domain pattern
    if _FARM_DOMAIN_RE.search(domain):
        return {"credibility_score": 0.0, "credibility_tier": "0A",
                "credibility_label": "Rejected", "source_domain": domain}

    # Tier 0-A: Content farm — title signals
    if title and (_FARM_TITLE_RE.search(title) or _is_all_caps_headline(title)):
        return {"credibility_score": 0.0, "credibility_tier": "0A",
                "credibility_label": "Rejected", "source_domain": domain}

    if _domain_in(domain, TIER1_DOMAINS):
        return {"credibility_score": 1.0, "credibility_tier": "1",
                "credibility_label": "Official source", "source_domain": domain}

    if _domain_in(domain, TIER2_DOMAINS):
        return {"credibility_score": 0.8, "credibility_tier": "2",
                "credibility_label": "Verified press", "source_domain": domain}

    if _domain_in(domain, TIER3_DOMAINS):
        return {"credibility_score": 0.5, "credibility_tier": "3",
                "credibility_label": "General press", "source_domain": domain}

    # Tier 0-B: Unknown — keep but flag unverified
    return {"credibility_score": 0.3, "credibility_tier": "0B",
            "credibility_label": "Unverified", "source_domain": domain or "unknown"}


def _is_all_caps_headline(title: str) -> bool:
    words = [w for w in title.split() if len(w) > 1]
    return len(words) >= 5 and sum(1 for w in words if w.isupper()) >= len(words) * 0.8

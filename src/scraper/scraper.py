"""
SEC EDGAR scraper for competitor filings.
Pulls 8-K (earnings announcements), 10-Q (quarterly), 10-K (annual) reports.
No API key required — SEC EDGAR is free and public.
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from config import TRANSCRIPTS_DIR

HEADERS = {"User-Agent": "ci-research@blueshield.com"}

COMPANIES = {
    "elevance": {
        "company_display": "Elevance Health",
        "cik": "0001156039",
        "ticker": "ELV",
    },
    "united": {
        "company_display": "UnitedHealth Group",
        "cik": "0000731766",
        "ticker": "UNH",
    },
    "aetna": {
        "company_display": "Aetna (CVS Health)",
        "cik": "0000064803",
        "ticker": "CVS",
    },
    "cigna": {
        "company_display": "Cigna Group",
        "cik": "0001739940",
        "ticker": "CI",
    },
    "humana": {
        "company_display": "Humana",
        "cik": "0000049071",
        "ticker": "HUM",
    },
    "centene": {
        "company_display": "Centene",
        "cik": "0001071739",
        "ticker": "CNC",
    },
    "molina": {
        "company_display": "Molina Healthcare",
        "cik": "0000916907",
        "ticker": "MOH",
    },
    "oscar": {
        "company_display": "Oscar Health",
        "cik": "0001568651",
        "ticker": "OSCR",
    },
}

EARNINGS_KEYWORDS = [
    "earnings", "results", "fourth quarter", "third quarter",
    "second quarter", "first quarter", "q1", "q2", "q3", "q4",
    "financial results", "quarterly results",
]

QUARTER_MAP = {1: "Q1", 2: "Q1", 3: "Q1",
               4: "Q2", 5: "Q2", 6: "Q2",
               7: "Q3", 8: "Q3", 9: "Q3",
               10: "Q4", 11: "Q4", 12: "Q4"}


def _month_to_quarter(month: int) -> str:
    return QUARTER_MAP.get(month, "Q1")


def _existing_periods(company: str) -> set[str]:
    company_dir = TRANSCRIPTS_DIR / company
    if not company_dir.exists():
        return set()
    periods = set()
    for f in company_dir.glob("*.txt"):
        parts = f.stem.rsplit(" ", 2)
        try:
            periods.add(f"{int(parts[-2])} {parts[-1]}")
        except (ValueError, IndexError):
            pass
    return periods


def _get_recent_filings(cik: str, form_type: str, max_results: int = 40) -> list[dict]:
    """Fetch recent filings of a given type from SEC EDGAR."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    d = r.json()

    recent = d["filings"]["recent"]
    results = []
    for i, form in enumerate(recent["form"]):
        if form != form_type:
            continue
        desc = recent.get("primaryDocDescription", [""] * len(recent["form"]))[i] or ""
        results.append({
            "form": form,
            "date": recent["filingDate"][i],
            "accession": recent["accessionNumber"][i],
            "primary_doc": recent["primaryDocument"][i],
            "description": desc,
        })
        if len(results) >= max_results:
            break
    return results


def _is_earnings_filing(filing: dict) -> bool:
    """Check if an 8-K is an earnings release (not a routine admin filing)."""
    desc = filing.get("description", "").lower()
    return any(kw in desc for kw in EARNINGS_KEYWORDS)


def _fetch_filing_text(cik: str, accession: str, primary_doc: str) -> str | None:
    """Download and parse a SEC filing to plain text."""
    cik_num = cik.lstrip("0")
    acc_clean = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{acc_clean}/{primary_doc}"
    try:
        time.sleep(0.5)
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"  [edgar] Failed to fetch {url}: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    # Remove script/style noise
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    text = "\n".join(lines)
    return text if len(text) > 300 else None


def _infer_quarter_from_date(date_str: str) -> tuple[int, str]:
    """Infer fiscal quarter from filing date (YYYY-MM-DD)."""
    month = int(date_str[5:7])
    year = int(date_str[:4])
    quarter = _month_to_quarter(month)
    # Earnings for Q are typically filed 1-2 months after quarter end
    # Q4 filings (Jan-Mar) → report prior year Q4
    if month <= 3:
        return year - 1, "Q4"
    return year, quarter


def scrape_company(company: str, form_types: list[str] = None) -> list[dict]:
    """Scrape new filings for a company. Returns list of newly saved docs."""
    if form_types is None:
        form_types = ["8-K", "10-Q"]

    info = COMPANIES[company]
    cik = info["cik"]
    company_display = info["company_display"]
    existing = _existing_periods(company)
    new_docs = []

    for form_type in form_types:
        print(f"  Checking {company_display} {form_type} filings...")
        try:
            filings = _get_recent_filings(cik, form_type, max_results=20)
        except Exception as e:
            print(f"  [edgar] Error fetching {form_type}: {e}")
            continue

        for filing in filings:
            # For 8-K, only take earnings-related ones
            if form_type == "8-K" and not _is_earnings_filing(filing):
                continue

            year, quarter = _infer_quarter_from_date(filing["date"])
            period = f"{year} {quarter}"

            if period in existing:
                continue

            print(f"  [edgar] New: {company_display} {period} ({form_type}, {filing['date']})")
            text = _fetch_filing_text(cik, filing["accession"], filing["primary_doc"])
            if not text:
                continue

            # Save
            company_dir = TRANSCRIPTS_DIR / company
            company_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{company_display} {year} {quarter}.txt"
            filepath = company_dir / filename
            filepath.write_text(
                f"Source: SEC EDGAR {form_type}\nDate: {filing['date']}\n\n{text}",
                encoding="utf-8"
            )
            existing.add(period)
            new_docs.append({
                "company": company,
                "company_display": company_display,
                "year": year,
                "quarter": quarter,
                "period": period,
                "form_type": form_type,
                "filing_date": filing["date"],
                "filepath": str(filepath),
            })
            print(f"  [edgar] Saved: {filename} ({len(text):,} chars)")
            time.sleep(0.3)

    return new_docs


def scrape_all_companies(form_types: list[str] = None) -> list[dict]:
    """Scrape all companies. Returns all newly saved docs."""
    all_new = []
    for company in COMPANIES:
        print(f"\nChecking {COMPANIES[company]['company_display']}...")
        new = scrape_company(company, form_types)
        all_new.extend(new)
    return all_new

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
VECTOR_DB_DIR = BASE_DIR / "data" / "vector_db"
LOGS_DIR = BASE_DIR / "data" / "logs"

TRANSCRIPTS_DIR = DATA_RAW / "transcripts"
TOPICS_FILE = BASE_DIR / "data" / "topics.json"

for _d in (VECTOR_DB_DIR, DATA_PROCESSED, LOGS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
TOP_K = 5
COLLECTION_NAME = "competitive_intelligence"

# All 10 tracked companies
COMPANIES_CONFIG = {
    "elevance": {
        "display_name": "Elevance Health",
        "sec_ticker": "ELV",
        "news_search_query": "Elevance Health health insurance",
        "official_ir_url": "https://ir.elevancehealth.com",
        "official_newsroom_url": "https://www.elevancehealth.com/newsroom",
    },
    "united": {
        "display_name": "UnitedHealth Group",
        "sec_ticker": "UNH",
        "news_search_query": "UnitedHealth Group health insurance",
        "official_ir_url": "https://ir.unitedhealthgroup.com",
        "official_newsroom_url": "https://www.unitedhealthgroup.com/newsroom.html",
    },
    "aetna": {
        "display_name": "Aetna (CVS Health)",
        "sec_ticker": "CVS",
        "news_search_query": "Aetna CVS Health insurance",
        "official_ir_url": "https://investors.cvshealth.com",
        "official_newsroom_url": "https://www.aetna.com/about-us/aetna-news.html",
    },
    "cigna": {
        "display_name": "Cigna Group",
        "sec_ticker": "CI",
        "news_search_query": "Cigna Group health insurance",
        "official_ir_url": "https://ir.cigna.com",
        "official_newsroom_url": "https://newsroom.cigna.com",
    },
    "humana": {
        "display_name": "Humana",
        "sec_ticker": "HUM",
        "news_search_query": "Humana Medicare health insurance",
        "official_ir_url": "https://ir.humana.com",
        "official_newsroom_url": "https://press.humana.com",
    },
    "centene": {
        "display_name": "Centene",
        "sec_ticker": "CNC",
        "news_search_query": "Centene Medicaid health insurance",
        "official_ir_url": "https://ir.centene.com",
        "official_newsroom_url": "https://www.centene.com/news.html",
    },
    "molina": {
        "display_name": "Molina Healthcare",
        "sec_ticker": "MOH",
        "news_search_query": "Molina Healthcare Medicaid",
        "official_ir_url": "https://ir.molinahealthcare.com",
        "official_newsroom_url": "https://www.molinahealthcare.com/about/newsroom",
    },
    "oscar": {
        "display_name": "Oscar Health",
        "sec_ticker": "OSCR",
        "news_search_query": "Oscar Health insurance",
        "official_ir_url": "https://ir.hioscar.com",
        "official_newsroom_url": "https://www.hioscar.com/blog",
    },
    "kaiser": {
        "display_name": "Kaiser Permanente",
        "sec_ticker": None,
        "news_search_query": "Kaiser Permanente health insurance",
        "official_ir_url": None,
        "official_newsroom_url": "https://about.kaiserpermanente.org/news",
    },
    "bluecross_ca": {
        "display_name": "Blue Cross (Anthem CA)",
        "sec_ticker": None,
        "news_search_query": "Anthem Blue Cross California health insurance",
        "official_ir_url": None,
        "official_newsroom_url": "https://www.anthem.com/press",
    },
}

COMPANIES = list(COMPANIES_CONFIG.keys())
COMPANY_DISPLAY = {k: v["display_name"] for k, v in COMPANIES_CONFIG.items()}

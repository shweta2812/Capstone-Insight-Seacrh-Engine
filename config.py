import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
VECTOR_DB_DIR = BASE_DIR / "data" / "vector_db"

TRANSCRIPTS_DIR = DATA_RAW / "transcripts"
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
TOP_K = 5
COLLECTION_NAME = "competitive_intelligence"

COMPANIES = ["elevance", "united"]
COMPANY_DISPLAY = {
    "elevance": "Elevance Health",
    "united": "UnitedHealth Group",
    "aetna": "Aetna (CVS Health)",
}

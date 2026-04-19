import re
from pathlib import Path
from config import TRANSCRIPTS_DIR, COMPANY_DISPLAY

NEWS_DIR = Path("data/raw/news")


def parse_filename(filepath: Path) -> dict:
    name = filepath.stem
    parts = name.rsplit(" ", 2)
    company_folder = filepath.parent.name
    # Detect if this is a news article (date_slug format: YYYY-MM-DD_...)
    is_news = re.match(r"^\d{4}-\d{2}-\d{2}_", name)
    if is_news:
        date_str = name[:10]
        title = name[11:].replace("-", " ")
        return {
            "company": company_folder,
            "company_display": COMPANY_DISPLAY.get(company_folder, company_folder),
            "year": int(date_str[:4]),
            "quarter": None,
            "period": date_str,
            "source_type": "news",
            "filename": filepath.name,
            "filepath": str(filepath),
        }
    try:
        year = int(parts[-2])
        quarter = parts[-1]
    except (ValueError, IndexError):
        year, quarter = None, None
    return {
        "company": company_folder,
        "company_display": COMPANY_DISPLAY.get(company_folder, company_folder),
        "year": year,
        "quarter": quarter,
        "period": f"{year} {quarter}" if year else name,
        "source_type": "sec_filing",
        "filename": filepath.name,
        "filepath": str(filepath),
    }


def load_transcript(filepath: Path) -> dict:
    text = filepath.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    meta = parse_filename(filepath)
    meta["text"] = text
    meta["char_count"] = len(text)
    return meta


def load_all_transcripts() -> list[dict]:
    docs = []
    for base_dir in [TRANSCRIPTS_DIR, NEWS_DIR]:
        if not base_dir.exists():
            continue
        for company_dir in sorted(base_dir.iterdir()):
            if not company_dir.is_dir():
                continue
            for txt_file in sorted(company_dir.glob("*.txt")):
                docs.append(load_transcript(txt_file))
    return docs

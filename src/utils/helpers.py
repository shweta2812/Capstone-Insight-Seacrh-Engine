import re


TOPIC_KEYWORDS = {
    "Membership": ["member", "enrollment", "subscriber", "lives covered", "membership"],
    "Revenue": ["revenue", "premium", "operating revenue", "top line"],
    "Medical Costs": ["medical loss ratio", "mlr", "medical costs", "claims"],
    "Technology": ["digital", "technology", "AI", "data analytics", "platform"],
    "Medicare": ["medicare", "medicare advantage", "CMS", "seniors"],
    "Medicaid": ["medicaid", "state-sponsored", "government programs"],
    "Commercial": ["commercial", "employer", "group insurance"],
    "Pharmacy": ["pharmacy", "PBM", "drug", "OptumRx", "Carelon"],
}


def extract_topics(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw.lower() in text_lower for kw in keywords):
            found.append(topic)
    return found


def quarter_to_month(quarter: str) -> int:
    return {"Q1": 3, "Q2": 6, "Q3": 9, "Q4": 12}.get(quarter, 1)


def sort_periods(periods: list[str]) -> list[str]:
    def key(p):
        parts = p.split()
        if len(parts) == 2:
            return (int(parts[0]), quarter_to_month(parts[1]))
        return (0, 0)
    return sorted(periods, key=key)

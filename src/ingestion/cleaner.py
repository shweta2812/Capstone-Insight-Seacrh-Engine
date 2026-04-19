import re


def clean_text(text: str) -> str:
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\(.*?inaudible.*?\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[-]{3,}", "", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_sections(text: str) -> dict:
    sections = {"prepared_remarks": "", "qa": "", "full": text}
    qa_split = re.split(
        r"(?i)(question[- ]and[- ]answer|q&a session|questions? and answers?)",
        text, maxsplit=1
    )
    if len(qa_split) >= 3:
        sections["prepared_remarks"] = qa_split[0].strip()
        sections["qa"] = (qa_split[1] + qa_split[2]).strip()
    else:
        sections["prepared_remarks"] = text
    return sections

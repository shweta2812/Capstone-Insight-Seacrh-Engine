from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP


_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def chunk_document(doc: dict) -> list[dict]:
    text = doc.get("text", "")
    chunks = _splitter.split_text(text)
    result = []
    for i, chunk in enumerate(chunks):
        chunk_doc = {k: v for k, v in doc.items() if k != "text"}
        chunk_doc["text"] = chunk
        chunk_doc["chunk_index"] = i
        source_key = doc.get("source_type", "doc")
        file_stem = doc.get("filename", f"{doc['company']}_{doc['year']}").rsplit(".", 1)[0]
        chunk_doc["chunk_id"] = f"{source_key}_{file_stem}_chunk{i}"
        result.append(chunk_doc)
    return result


def chunk_all_documents(docs: list[dict]) -> list[dict]:
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    return all_chunks

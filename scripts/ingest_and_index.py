"""Run once to parse, chunk, and index all transcripts into ChromaDB."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.loader import load_all_transcripts
from src.ingestion.cleaner import clean_text
from src.chunking.chunker import chunk_all_documents
from src.vector_store.chroma_store import index_chunks, collection_stats


def main():
    print("Loading transcripts...")
    docs = load_all_transcripts()
    print(f"  Loaded {len(docs)} documents")

    print("Cleaning text...")
    for doc in docs:
        doc["text"] = clean_text(doc["text"])

    print("Chunking documents...")
    chunks = chunk_all_documents(docs)
    print(f"  Created {len(chunks)} chunks")

    print("Indexing into ChromaDB...")
    index_chunks(chunks)

    stats = collection_stats()
    print(f"\nDone! Vector DB now has {stats['total_chunks']} chunks indexed.")


if __name__ == "__main__":
    main()

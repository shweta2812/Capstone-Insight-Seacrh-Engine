#!/bin/bash
cd "$(dirname "$0")"

# Step 1: Install dependencies
pip install -r requirements.txt -q

# Step 2: Index documents (skip if already done)
if [ ! -d "data/vector_db/chroma.sqlite3" ]; then
    echo "Indexing documents..."
    python scripts/ingest_and_index.py
fi

# Step 3: Launch app
streamlit run app/main.py

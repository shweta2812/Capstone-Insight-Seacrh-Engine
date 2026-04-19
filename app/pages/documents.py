import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
from src.ingestion.loader import load_all_transcripts


def render():
    st.markdown("""
    <div class="hero-banner">
        <h2>Document Library</h2>
        <p>Browse and search all indexed competitive intelligence documents</p>
    </div>
    """, unsafe_allow_html=True)

    docs = load_all_transcripts()
    if not docs:
        st.info("No documents found.")
        return

    # Filters
    col1, col2, col3 = st.columns(3)
    companies = ["All"] + sorted(set(d["company_display"] for d in docs))
    years = ["All"] + sorted(set(str(d["year"]) for d in docs if d["year"]), reverse=True)

    with col1:
        co_filter = st.selectbox("Company", companies)
    with col2:
        yr_filter = st.selectbox("Year", years)
    with col3:
        search_text = st.text_input("Search filename", placeholder="e.g. 2024 Q3")

    filtered = docs
    if co_filter != "All":
        filtered = [d for d in filtered if d["company_display"] == co_filter]
    if yr_filter != "All":
        filtered = [d for d in filtered if str(d["year"]) == yr_filter]
    if search_text:
        filtered = [d for d in filtered if search_text.lower() in d["filename"].lower()]

    st.markdown(f'<p class="section-header">Showing {len(filtered)} documents</p>', unsafe_allow_html=True)

    df = pd.DataFrame(filtered)[["company_display", "year", "quarter", "period", "source_type", "char_count", "filename"]]
    df = df.sort_values(["year", "quarter"], ascending=[False, False])
    df.columns = ["Company", "Year", "Quarter", "Period", "Source Type", "Characters", "Filename"]
    df["Characters"] = df["Characters"].apply(lambda x: f"{x:,}")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown('<p class="section-header">Preview Document</p>', unsafe_allow_html=True)

    periods = [f"{d['company_display']} — {d['period']}" for d in filtered]
    if periods:
        selected_label = st.selectbox("Select document to preview", periods)
        idx = periods.index(selected_label)
        doc = filtered[idx]
        st.markdown(f"""
        <div style="background:white;border-radius:10px;padding:14px 18px;margin-bottom:12px;border:1px solid #e8eaf6;">
            <b>{doc['company_display']}</b> · {doc['period']} · {doc['source_type']}
            <span style="float:right;color:#888;font-size:13px;">{doc['char_count']:,} characters</span>
        </div>
        """, unsafe_allow_html=True)
        preview_len = st.slider("Preview length (characters)", 500, 5000, 1500, step=500)
        st.text_area("Document text", doc["text"][:preview_len], height=300, label_visibility="collapsed")

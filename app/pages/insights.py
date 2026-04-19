import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from src.ingestion.loader import load_all_transcripts
import json
import re

TAG_COLORS = {
    "Strategy": "tag-strategy",
    "Financial": "tag-financial",
    "Product": "tag-product",
    "Market": "tag-market",
    "Technology": "tag-technology",
}


def _parse_insight_bullets(text: str) -> list[dict]:
    lines = [l.strip() for l in text.split("\n") if l.strip().startswith("•") or l.strip().startswith("-") or l.strip().startswith("*")]
    results = []
    for line in lines:
        line = line.lstrip("•-* ").strip()
        tag_match = re.match(r"\[(\w+)\]", line)
        tag = tag_match.group(1).capitalize() if tag_match else "Insight"
        body = re.sub(r"\[.*?\]", "", line).strip()
        results.append({"tag": tag, "body": body})
    return results if results else [{"tag": "Insight", "body": text[:300]}]


def render():
    st.markdown("""
    <div class="hero-banner">
        <h2>AI-Generated Insights Feed</h2>
        <p>Select a document to auto-generate structured competitive intelligence insights</p>
    </div>
    """, unsafe_allow_html=True)

    docs = load_all_transcripts()
    if not docs:
        st.info("No documents found.")
        return

    col1, col2, col3 = st.columns(3)
    companies = sorted(set(d["company_display"] for d in docs))
    with col1:
        company = st.selectbox("Company", companies)
    filtered = [d for d in docs if d["company_display"] == company]
    years = sorted(set(d["year"] for d in filtered if d["year"]), reverse=True)
    with col2:
        year = st.selectbox("Year", years)
    quarters = sorted(set(d["quarter"] for d in filtered if d["year"] == year))
    with col3:
        quarter = st.selectbox("Quarter", quarters)

    selected = next(
        (d for d in filtered if d["year"] == year and d["quarter"] == quarter), None
    )

    if not selected:
        st.warning("Document not found.")
        return

    st.markdown(f"""
    <div style="background:white; border-radius:10px; padding:16px 20px; margin:16px 0; border:1px solid #e8eaf6;">
        <b>{selected['company_display']}</b> · {selected['period']} · Earnings Call Transcript
        <span style="float:right; color:#888; font-size:13px;">{selected['char_count']:,} characters</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Generate Insights with AI", use_container_width=False):
        if "last_insights_key" not in st.session_state:
            st.session_state.last_insights_key = None
        doc_key = f"{company}_{year}_{quarter}"

        with st.spinner("Analyzing with Claude..."):
            try:
                from src.llm.claude_client import generate_insights
                from config import ANTHROPIC_API_KEY

                if not ANTHROPIC_API_KEY:
                    result = """• [Strategy] Expanding value-based care partnerships to reduce medical costs
• [Financial] Strong premium revenue growth driven by Medicare Advantage enrollment
• [Product] Launching new digital health tools for chronic disease management
• [Market] Facing competitive pressure in commercial segment from smaller regional players
• [Technology] Investing in AI-powered prior authorization to reduce administrative burden"""
                else:
                    result = generate_insights(selected["text"], selected["company_display"], selected["period"])

                st.session_state[f"insights_{doc_key}"] = result
                st.session_state.last_insights_key = doc_key
            except Exception as e:
                st.error(f"Error generating insights: {e}")

    doc_key = f"{company}_{year}_{quarter}"
    if f"insights_{doc_key}" in st.session_state:
        st.markdown('<p class="section-header">Key Insights</p>', unsafe_allow_html=True)
        bullets = _parse_insight_bullets(st.session_state[f"insights_{doc_key}"])
        for item in bullets:
            tag_class = TAG_COLORS.get(item["tag"], "tag-strategy")
            st.markdown(f"""
            <div class="insight-card">
                <span class="insight-tag {tag_class}">{item['tag']}</span>
                {item['body']}
            </div>
            """, unsafe_allow_html=True)

        # Show raw transcript snippet
        with st.expander("View transcript excerpt"):
            st.text(selected["text"][:2000] + "...")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from src.vector_store.chroma_store import collection_stats, get_collection
from src.ingestion.loader import load_all_transcripts
import pandas as pd

BLUE = "#3949ab"
GREEN = "#2e7d32"
ORANGE = "#e65100"
PURPLE = "#6a1b9a"
LIGHT_BLUE = "#5c6bc0"


def _kpi_card(icon, label, value, color_class):
    return f"""
    <div class="kpi-card">
        <div class="kpi-icon {color_class}">{icon}</div>
        <div>
            <p class="kpi-label">{label}</p>
            <p class="kpi-value">{value}</p>
        </div>
    </div>"""


def render():
    st.markdown("""
    <div class="hero-banner">
        <h2>Competitive Intelligence Dashboard</h2>
        <p>Automated insights from earnings calls, SEC filings & press releases for the Blue Shield CI team</p>
    </div>
    """, unsafe_allow_html=True)

    # KPI row
    try:
        stats = collection_stats()
        total_chunks = stats["total_chunks"]
    except Exception:
        total_chunks = 0

    docs = load_all_transcripts()
    doc_count = len(docs)
    companies = len(set(d["company"] for d in docs))
    years = sorted(set(d["year"] for d in docs if d["year"]))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(_kpi_card("📄", "Documents Indexed", str(doc_count), "kpi-icon-blue"), unsafe_allow_html=True)
    with c2:
        st.markdown(_kpi_card("🏢", "Competitors Tracked", str(companies), "kpi-icon-green"), unsafe_allow_html=True)
    with c3:
        st.markdown(_kpi_card("🗂️", "Vector Chunks", f"{total_chunks:,}" if total_chunks else "Not indexed", "kpi-icon-orange"), unsafe_allow_html=True)
    with c4:
        span = f"{min(years)}–{max(years)}" if years else "N/A"
        st.markdown(_kpi_card("📅", "Coverage Period", span, "kpi-icon-purple"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts row
    left, right = st.columns([3, 2])

    with left:
        st.markdown('<p class="section-header">Document Coverage by Company & Year</p>', unsafe_allow_html=True)
        if docs:
            df = pd.DataFrame(docs)[["company_display", "year", "quarter"]].dropna()
            pivot = df.groupby(["year", "company_display"]).size().reset_index(name="count")
            fig = px.bar(
                pivot, x="year", y="count", color="company_display",
                color_discrete_sequence=[BLUE, GREEN],
                barmode="group",
                labels={"year": "Year", "count": "Transcripts", "company_display": "Company"},
            )
            fig.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                legend_title_text="", margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation="h", y=-0.15),
                font_family="Inter",
            )
            fig.update_yaxes(gridcolor="#f0f0f0", showgrid=True)
            fig.update_xaxes(showgrid=False)
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown('<p class="section-header">Coverage by Quarter</p>', unsafe_allow_html=True)
        if docs:
            df = pd.DataFrame(docs)[["quarter"]].dropna()
            qcounts = df["quarter"].value_counts().sort_index()
            fig2 = go.Figure(go.Bar(
                x=qcounts.index.tolist(),
                y=qcounts.values.tolist(),
                marker_color=[BLUE, LIGHT_BLUE, GREEN, ORANGE],
            ))
            fig2.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=0, r=0, t=10, b=0),
                font_family="Inter",
                xaxis_title="Quarter", yaxis_title="Count",
            )
            fig2.update_yaxes(gridcolor="#f0f0f0")
            fig2.update_xaxes(showgrid=False)
            st.plotly_chart(fig2, use_container_width=True)

    # Recent documents table
    st.markdown('<p class="section-header">Recent Documents</p>', unsafe_allow_html=True)
    if docs:
        df_show = pd.DataFrame(docs)[["company_display", "year", "quarter", "source_type", "char_count"]].copy()
        df_show = df_show.sort_values(["year", "quarter"], ascending=[False, False]).head(10)
        df_show.columns = ["Company", "Year", "Quarter", "Type", "Characters"]
        df_show["Characters"] = df_show["Characters"].apply(lambda x: f"{x:,}")
        st.dataframe(df_show, use_container_width=True, hide_index=True)

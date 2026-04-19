import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import re
from src.ingestion.loader import load_all_transcripts
from src.utils.helpers import TOPIC_KEYWORDS, sort_periods

BLUE = "#3949ab"
GREEN = "#2e7d32"
COLORS = [BLUE, GREEN, "#e65100", "#6a1b9a", "#00695c", "#c62828"]


def _count_keyword(text: str, keywords: list[str]) -> int:
    text_lower = text.lower()
    return sum(len(re.findall(r'\b' + re.escape(kw.lower()) + r'\b', text_lower)) for kw in keywords)


def render():
    st.markdown("""
    <div class="hero-banner">
        <h2>Trend Analysis</h2>
        <p>Track how key topics and themes evolve across competitors over time</p>
    </div>
    """, unsafe_allow_html=True)

    docs = load_all_transcripts()
    if not docs:
        st.info("No documents found.")
        return

    tab1, tab2, tab3 = st.tabs(["Topic Trends", "Document Volume", "Word Frequency"])

    with tab1:
        st.markdown('<p class="section-header">Topic Mention Frequency Over Time</p>', unsafe_allow_html=True)

        topics = list(TOPIC_KEYWORDS.keys())
        selected_topics = st.multiselect("Select topics to track", topics, default=topics[:4])
        companies = sorted(set(d["company_display"] for d in docs))
        selected_companies = st.multiselect("Companies", companies, default=companies)

        if selected_topics and selected_companies:
            rows = []
            for doc in docs:
                if doc["company_display"] not in selected_companies:
                    continue
                for topic in selected_topics:
                    count = _count_keyword(doc["text"], TOPIC_KEYWORDS[topic])
                    rows.append({
                        "period": doc["period"],
                        "year": doc["year"],
                        "quarter": doc["quarter"],
                        "company": doc["company_display"],
                        "topic": topic,
                        "mentions": count,
                    })
            df = pd.DataFrame(rows)
            df = df.sort_values(["year", "quarter"])

            for topic in selected_topics:
                topic_df = df[df["topic"] == topic]
                fig = go.Figure()
                for i, company in enumerate(selected_companies):
                    cdf = topic_df[topic_df["company"] == company].groupby("period")["mentions"].sum().reset_index()
                    cdf["period_sorted"] = pd.Categorical(
                        cdf["period"],
                        categories=sort_periods(cdf["period"].tolist()),
                        ordered=True,
                    )
                    cdf = cdf.sort_values("period_sorted")
                    fig.add_trace(go.Scatter(
                        x=cdf["period"], y=cdf["mentions"],
                        name=company, mode="lines+markers",
                        line=dict(color=COLORS[i % len(COLORS)], width=2),
                        marker=dict(size=6),
                    ))
                fig.update_layout(
                    title=f"{topic} Mentions",
                    plot_bgcolor="white", paper_bgcolor="white",
                    font_family="Inter",
                    margin=dict(l=0, r=0, t=40, b=60),
                    legend=dict(orientation="h", y=-0.25),
                    xaxis=dict(tickangle=-45),
                )
                fig.update_yaxes(gridcolor="#f0f0f0")
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown('<p class="section-header">Transcripts Published Per Year</p>', unsafe_allow_html=True)
        df_vol = pd.DataFrame(docs)[["company_display", "year"]].dropna()
        vol = df_vol.groupby(["year", "company_display"]).size().reset_index(name="count")
        fig2 = px.line(
            vol, x="year", y="count", color="company_display",
            markers=True,
            color_discrete_sequence=[BLUE, GREEN],
            labels={"year": "Year", "count": "Transcripts", "company_display": "Company"},
        )
        fig2.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            font_family="Inter", margin=dict(l=0, r=0, t=10, b=0),
            legend_title_text="",
        )
        fig2.update_yaxes(gridcolor="#f0f0f0")
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.markdown('<p class="section-header">Custom Keyword Frequency</p>', unsafe_allow_html=True)
        keyword = st.text_input("Enter a keyword or phrase to track:", placeholder="e.g. artificial intelligence")
        if keyword:
            rows = []
            for doc in docs:
                count = _count_keyword(doc["text"], [keyword])
                rows.append({
                    "period": doc["period"],
                    "year": doc["year"],
                    "quarter": doc["quarter"],
                    "company": doc["company_display"],
                    "mentions": count,
                })
            df_kw = pd.DataFrame(rows).sort_values(["year", "quarter"])
            fig3 = go.Figure()
            for i, company in enumerate(sorted(df_kw["company"].unique())):
                cdf = df_kw[df_kw["company"] == company]
                fig3.add_trace(go.Bar(
                    x=cdf["period"], y=cdf["mentions"],
                    name=company, marker_color=COLORS[i % len(COLORS)],
                ))
            fig3.update_layout(
                barmode="group", plot_bgcolor="white", paper_bgcolor="white",
                font_family="Inter", margin=dict(l=0, r=0, t=10, b=80),
                xaxis=dict(tickangle=-45), legend_title_text="",
            )
            fig3.update_yaxes(gridcolor="#f0f0f0")
            st.plotly_chart(fig3, use_container_width=True)

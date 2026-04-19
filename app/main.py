import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
st.set_page_config(
    page_title="CI Insights Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.styles import HOPE_UI_CSS
st.markdown(HOPE_UI_CSS, unsafe_allow_html=True)

from app.pages import dashboard, search, insights, trends, documents

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 16px 0 24px 0; text-align:center;">
        <div style="font-size:28px;">🔍</div>
        <div style="font-size:17px; font-weight:700; color:white; margin-top:4px;">CI Insights Engine</div>
        <div style="font-size:12px; color:rgba(255,255,255,0.6); margin-top:2px;">Blue Shield of California</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("HOME")
    nav = st.radio(
        "",
        options=["Dashboard", "Ask / Search", "Insights Feed", "Trends", "Documents"],
        label_visibility="collapsed",
        format_func=lambda x: {
            "Dashboard": "  Dashboard",
            "Ask / Search": "  Ask / Search",
            "Insights Feed": "  Insights Feed",
            "Trends": "  Trends",
            "Documents": "  Documents",
        }[x],
    )

    st.markdown("---")
    st.markdown("COMPETITORS TRACKED")
    st.markdown("""
    <div style="padding: 4px 12px;">
        <div style="color: rgba(255,255,255,0.9); font-size:13px; padding: 4px 0;">🏥 Elevance Health</div>
        <div style="color: rgba(255,255,255,0.9); font-size:13px; padding: 4px 0;">🏥 UnitedHealth Group</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="padding: 12px; text-align:center;">
        <div style="color:rgba(255,255,255,0.5); font-size:11px;">Blue Shield of California</div>
        <div style="color:rgba(255,255,255,0.5); font-size:11px;">Competitive Intelligence Team</div>
    </div>
    """, unsafe_allow_html=True)

# ── Page routing ──────────────────────────────────────────────────────────────
if nav == "Dashboard":
    dashboard.render()
elif nav == "Ask / Search":
    search.render()
elif nav == "Insights Feed":
    insights.render()
elif nav == "Trends":
    trends.render()
elif nav == "Documents":
    documents.render()

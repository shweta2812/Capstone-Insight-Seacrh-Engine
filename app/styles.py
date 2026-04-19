HOPE_UI_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide default Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
header[data-testid="stHeader"] {background: transparent;}

/* Main background */
.stApp {
    background-color: #f0f2f5;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a237e 0%, #283593 40%, #3949ab 100%);
    border-right: none;
}
[data-testid="stSidebar"] * {
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: rgba(255,255,255,0.7) !important;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 16px;
    margin-bottom: 4px;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.15) !important;
}
[data-testid="stSidebarNav"] {display: none;}

/* Radio buttons as nav items */
[data-testid="stSidebar"] .stRadio label {
    background: transparent;
    border-radius: 8px;
    padding: 8px 12px;
    display: block;
    cursor: pointer;
    transition: background 0.2s;
    color: rgba(255,255,255,0.85) !important;
    font-weight: 500;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.12);
}
[data-testid="stSidebar"] [aria-checked="true"] + label,
[data-testid="stSidebar"] .stRadio [data-checked="true"] label {
    background: rgba(255,255,255,0.2) !important;
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
    gap: 2px;
}

/* KPI Cards */
.kpi-card {
    background: white;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    display: flex;
    align-items: center;
    gap: 16px;
    border: 1px solid #f0f0f0;
}
.kpi-icon {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
}
.kpi-icon-blue { background: #e8eaf6; color: #3949ab; }
.kpi-icon-green { background: #e8f5e9; color: #2e7d32; }
.kpi-icon-orange { background: #fff3e0; color: #e65100; }
.kpi-icon-purple { background: #f3e5f5; color: #6a1b9a; }
.kpi-label { font-size: 13px; color: #888; font-weight: 400; margin: 0; }
.kpi-value { font-size: 26px; font-weight: 700; color: #1a237e; margin: 0; }

/* Section headers */
.section-header {
    font-size: 18px;
    font-weight: 600;
    color: #1a237e;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #e8eaf6;
}

/* Hero banner */
.hero-banner {
    background: linear-gradient(135deg, #1a237e 0%, #3949ab 60%, #5c6bc0 100%);
    border-radius: 16px;
    padding: 28px 32px;
    color: white;
    margin-bottom: 24px;
}
.hero-banner h2 { margin: 0 0 6px 0; font-size: 24px; font-weight: 700; }
.hero-banner p { margin: 0; opacity: 0.85; font-size: 14px; }

/* Chat bubbles */
.chat-user {
    background: #e8eaf6;
    border-radius: 12px 12px 2px 12px;
    padding: 12px 16px;
    margin: 8px 0;
    margin-left: 15%;
    color: #1a237e;
    font-weight: 500;
}
.chat-bot {
    background: white;
    border-radius: 12px 12px 12px 2px;
    padding: 12px 16px;
    margin: 8px 0;
    margin-right: 10%;
    border: 1px solid #e8eaf6;
    color: #333;
}

/* Citation pills */
.citation {
    display: inline-block;
    background: #e8eaf6;
    color: #3949ab;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 600;
    margin: 2px;
}

/* Insight card */
.insight-card {
    background: white;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 10px;
    border-left: 4px solid #3949ab;
    box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}
.insight-tag {
    display: inline-block;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    margin-right: 6px;
}
.tag-strategy { background: #e8eaf6; color: #3949ab; }
.tag-financial { background: #e8f5e9; color: #2e7d32; }
.tag-product { background: #fff3e0; color: #e65100; }
.tag-market { background: #fce4ec; color: #c62828; }
.tag-technology { background: #e0f2f1; color: #00695c; }

/* Tables */
.stDataFrame { border-radius: 10px; overflow: hidden; }

/* Buttons */
.stButton button {
    background: #3949ab !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
}
.stButton button:hover {
    background: #1a237e !important;
}

/* Select/input */
.stSelectbox div[data-baseweb="select"] > div,
.stTextInput input, .stTextArea textarea {
    border-radius: 8px !important;
    border-color: #e0e0e0 !important;
}
.stSelectbox div[data-baseweb="select"] > div:focus-within,
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #3949ab !important;
    box-shadow: 0 0 0 2px rgba(57,73,171,0.15) !important;
}
</style>
"""

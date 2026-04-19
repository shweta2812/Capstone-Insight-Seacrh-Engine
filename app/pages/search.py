import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st


def render():
    st.markdown("""
    <div class="hero-banner">
        <h2>Ask the Insights Engine</h2>
        <p>Ask any question about competitor strategy, financials, or products — grounded in real documents</p>
    </div>
    """, unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "search_ready" not in st.session_state:
        st.session_state.search_ready = False

    try:
        from src.vector_store.chroma_store import collection_stats
        stats = collection_stats()
        if stats["total_chunks"] > 0:
            st.session_state.search_ready = True
    except Exception:
        pass

    if not st.session_state.search_ready:
        st.warning("Vector database is empty. Run `python scripts/ingest_and_index.py` first to index documents.")

    # Filters
    with st.expander("Filters (optional)", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            company_filter = st.selectbox(
                "Company", ["All", "Elevance Health", "UnitedHealth Group"]
            )
        with col2:
            year_filter = st.selectbox(
                "Year", ["All"] + [str(y) for y in range(2025, 2019, -1)]
            )

    # Suggested questions
    st.markdown('<p class="section-header">Suggested Questions</p>', unsafe_allow_html=True)
    suggestions = [
        "What are Elevance's key strategic priorities for 2024?",
        "How is UnitedHealth growing Medicare Advantage membership?",
        "What technology investments are competitors making?",
        "Compare medical loss ratios between Elevance and United.",
        "What did competitors say about Medicaid redeterminations?",
    ]
    cols = st.columns(len(suggestions))
    selected_suggestion = None
    for i, (col, sug) in enumerate(zip(cols, suggestions)):
        with col:
            if st.button(sug, key=f"sug_{i}", use_container_width=True):
                selected_suggestion = sug

    # Chat history display
    if st.session_state.chat_history:
        st.markdown('<p class="section-header">Conversation</p>', unsafe_allow_html=True)
        for turn in st.session_state.chat_history:
            st.markdown(f'<div class="chat-user">{turn["question"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-bot">{turn["answer"]}</div>', unsafe_allow_html=True)
            if turn.get("citations"):
                citation_html = "".join(
                    f'<span class="citation">[{c["ref"]}] {c["company"]} · {c["period"]}</span>'
                    for c in turn["citations"]
                )
                st.markdown(f"<div style='margin: 4px 0 12px 0;'>{citation_html}</div>", unsafe_allow_html=True)

    # Input
    st.markdown('<p class="section-header">Your Question</p>', unsafe_allow_html=True)
    default_val = selected_suggestion or ""
    question = st.text_area(
        "Ask anything about competitor strategy, financials, products, or market positioning:",
        value=default_val,
        height=90,
        placeholder="e.g. What growth strategies is Elevance pursuing in 2024?",
    )

    col_ask, col_clear = st.columns([1, 5])
    with col_ask:
        ask_clicked = st.button("Ask", use_container_width=True)
    with col_clear:
        if st.button("Clear history"):
            st.session_state.chat_history = []
            st.rerun()

    if ask_clicked and question.strip():
        if not st.session_state.search_ready:
            st.error("Please index documents first.")
        else:
            with st.spinner("Searching and generating answer..."):
                try:
                    from src.retrieval.retriever import hybrid_search, get_context_string, format_citations
                    from src.llm.claude_client import answer_question
                    from config import ANTHROPIC_API_KEY

                    filters = {}
                    if company_filter != "All":
                        company_map = {"Elevance Health": "elevance", "UnitedHealth Group": "united"}
                        filters["company"] = company_map[company_filter]
                    if year_filter != "All":
                        filters["year"] = year_filter

                    hits = hybrid_search(question, filters=filters if filters else None)
                    context = get_context_string(hits)
                    citations = format_citations(hits)

                    if not ANTHROPIC_API_KEY:
                        answer = f"**[Demo mode — no API key]**\n\nFound {len(hits)} relevant chunks. Top source: {citations[0]['company']} {citations[0]['period'] if citations else ''}.\n\nAdd your ANTHROPIC_API_KEY to .env to enable AI-generated answers."
                    else:
                        answer = answer_question(question, context, st.session_state.chat_history)

                    st.session_state.chat_history.append({
                        "question": question,
                        "answer": answer,
                        "citations": citations,
                    })
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

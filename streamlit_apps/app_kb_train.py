"""
Knowledge Base Training App - Feed data into the RAG knowledge base.

Features:
  1. Add custom market insights / research notes
  2. Upload JSON data files for any category
  3. Feed outcome data to teach the RAG (learn from returns)
  4. View & manage KB contents
  5. Bulk import from files
"""
import streamlit as st
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from multi_rag.rag_manager import RAGManager
from multi_rag.explainability import Explainability
from agents.kb_agent import KnowledgeBaseAgent
from dataflows.data_loader import DataLoader
from preferences import SUPPORTED_TICKERS

st.set_page_config(page_title="KB Training", page_icon="🧠", layout="wide")
st.title("🧠 Knowledge Base Training & Management")
st.markdown("*Feed data, teach lessons, and manage the RAG knowledge base*")


@st.cache_resource
def get_rag():
    return RAGManager()


rag = get_rag()
kb = KnowledgeBaseAgent(rag)
explainer = Explainability(rag)
loader = DataLoader()

# ──────────────────────────────────────────────────────────────────
tab_add, tab_teach, tab_upload, tab_browse, tab_manage = st.tabs(
    ["📝 Add Knowledge", "🎓 Teach Outcomes", "📤 Upload Data", "🔍 Browse KB", "🗑️ Manage"]
)

# ──────────────────────────────────────────────────────────────────
# Tab 1: Add custom knowledge / insights
# ──────────────────────────────────────────────────────────────────
with tab_add:
    st.header("Add Custom Market Insights")
    st.caption(
        "Add research notes, analysis, or any insight you want the agents "
        "to retrieve in future analyses."
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        add_ticker = st.selectbox("Ticker", SUPPORTED_TICKERS, key="add_ticker")
        add_store = st.selectbox(
            "Store",
            ["market_insights", "trade_history", "lessons_learned"],
            key="add_store",
        )
    with col2:
        add_text = st.text_area(
            "Knowledge / Insight",
            height=200,
            placeholder="e.g., AAPL showed strong resistance at $195 during Q4 2024. "
            "iPhone 16 sales exceeded expectations by 12%...",
        )

    if st.button("➕ Add to Knowledge Base", type="primary"):
        if add_text.strip():
            if add_store == "market_insights":
                doc_id = kb.add_custom_knowledge(add_ticker, add_text)
            elif add_store == "trade_history":
                doc_id = rag.store_decision(
                    ticker=add_ticker,
                    date=datetime.now().strftime("%Y-%m-%d"),
                    decision="NOTE",
                    reasoning=add_text,
                )
            else:
                doc_id = rag.store_lesson(
                    ticker=add_ticker,
                    date=datetime.now().strftime("%Y-%m-%d"),
                    lesson=add_text,
                    was_correct=True,
                )
            st.success(f"✅ Added! Document ID: {doc_id}")
        else:
            st.warning("Please enter some text.")

# ──────────────────────────────────────────────────────────────────
# Tab 2: Teach from outcomes (the learning loop)
# ──────────────────────────────────────────────────────────────────
with tab_teach:
    st.header("🎓 Teach the RAG from Actual Outcomes")
    st.caption(
        "Tell the system what actually happened after a decision. "
        "This creates lessons that improve future analyses."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        teach_ticker = st.selectbox("Ticker", SUPPORTED_TICKERS, key="teach_ticker")
    with col2:
        teach_date = st.date_input("Decision Date", key="teach_date")
    with col3:
        teach_decision = st.selectbox("Decision Made", ["BUY", "SELL", "HOLD"])

    teach_reasoning = st.text_area("Original Reasoning", height=100)
    teach_return = st.number_input(
        "Actual Return (%)",
        min_value=-100.0,
        max_value=500.0,
        value=0.0,
        step=0.1,
        help="e.g., 5.0 means +5%, -3.2 means -3.2%",
    )

    if st.button("📚 Store Lesson", type="primary"):
        lesson_id = explainer.learn_from_outcome(
            ticker=teach_ticker,
            date=teach_date.strftime("%Y-%m-%d"),
            decision=teach_decision,
            reasoning=teach_reasoning,
            actual_return=teach_return / 100.0,
        )
        st.success(f"✅ Lesson stored! ID: {lesson_id}")
        was_correct = (
            (teach_decision == "BUY" and teach_return > 0)
            or (teach_decision == "SELL" and teach_return < 0)
            or (teach_decision == "HOLD" and abs(teach_return) < 5)
        )
        if was_correct:
            st.balloons()
            st.info("The decision was CORRECT based on actual returns.")
        else:
            st.warning("The decision was WRONG. This lesson will help future analyses.")

# ──────────────────────────────────────────────────────────────────
# Tab 3: Upload JSON data files
# ──────────────────────────────────────────────────────────────────
with tab_upload:
    st.header("📤 Upload Data Files")
    st.caption("Upload JSON files to populate data directories for agents.")

    col1, col2, col3 = st.columns(3)
    with col1:
        up_ticker = st.selectbox("Ticker", SUPPORTED_TICKERS, key="up_ticker")
    with col2:
        up_type = st.selectbox(
            "Data Type", ["fundamentals", "market", "news", "social"]
        )
    with col3:
        up_date = st.date_input("Date (optional)", key="up_date")
        up_use_date = st.checkbox("Include date in filename")

    uploaded_file = st.file_uploader("Upload JSON file", type=["json"])

    if uploaded_file and st.button("💾 Save Data File"):
        try:
            data = json.load(uploaded_file)
            date_val = up_date.strftime("%Y-%m-%d") if up_use_date else None
            path = loader.save_json(up_ticker, up_type, data, date_val)
            st.success(f"✅ Saved to: {path}")
        except json.JSONDecodeError:
            st.error("Invalid JSON file.")

    st.markdown("---")
    st.subheader("📝 Or paste JSON directly")
    paste_json = st.text_area("Paste JSON data", height=200, key="paste_json")
    if paste_json and st.button("💾 Save Pasted Data"):
        try:
            data = json.loads(paste_json)
            date_val = up_date.strftime("%Y-%m-%d") if up_use_date else None
            path = loader.save_json(up_ticker, up_type, data, date_val)
            st.success(f"✅ Saved to: {path}")
        except json.JSONDecodeError:
            st.error("Invalid JSON.")

    # Also allow adding text directly to RAG as an insight
    st.markdown("---")
    st.subheader("📎 Bulk add insights from text")
    bulk_text = st.text_area(
        "Paste multiple insights (one per paragraph, separated by blank lines)",
        height=200,
        key="bulk_text",
    )
    bulk_ticker = st.selectbox("For Ticker", SUPPORTED_TICKERS, key="bulk_ticker")
    if bulk_text and st.button("📚 Bulk Add to KB"):
        paragraphs = [p.strip() for p in bulk_text.split("\n\n") if p.strip()]
        for p in paragraphs:
            kb.add_custom_knowledge(bulk_ticker, p)
        st.success(f"✅ Added {len(paragraphs)} insights for {bulk_ticker}!")

# ──────────────────────────────────────────────────────────────────
# Tab 4: Browse KB contents
# ──────────────────────────────────────────────────────────────────
with tab_browse:
    st.header("🔍 Browse Knowledge Base")

    browse_col1, browse_col2 = st.columns(2)
    with browse_col1:
        browse_query = st.text_input("Search query", "latest analysis")
    with browse_col2:
        browse_store = st.selectbox(
            "Store",
            ["All", "market_insights", "trade_history", "lessons_learned"],
            key="browse_store",
        )

    n_results = st.slider("Max results per store", 1, 20, 5)

    if st.button("🔎 Search", type="primary"):
        with st.spinner("Searching…"):
            if browse_store == "All":
                results = rag.query_all(browse_query, n_per_store=n_results)
                for store_name, docs in results.items():
                    st.subheader(f"📂 {store_name} ({len(docs)} results)")
                    for i, doc in enumerate(docs):
                        with st.expander(
                            f"Result {i + 1} — distance: {doc.get('distance', 'N/A')}"
                        ):
                            st.text(doc["text"])
                            st.json(doc.get("metadata", {}))
                if not results:
                    st.info("No results found. Add some knowledge first!")
            else:
                results = rag.query(browse_store, browse_query, n=n_results)
                st.subheader(f"📂 {browse_store} ({len(results)} results)")
                for i, doc in enumerate(results):
                    with st.expander(
                        f"Result {i + 1} — distance: {doc.get('distance', 'N/A')}"
                    ):
                        st.text(doc["text"])
                        st.json(doc.get("metadata", {}))

# ──────────────────────────────────────────────────────────────────
# Tab 5: Manage / clear
# ──────────────────────────────────────────────────────────────────
with tab_manage:
    st.header("🗑️ Manage Knowledge Base")

    stats = rag.get_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("📚 Market Insights", stats.get("market_insights", 0))
    c2.metric("📜 Trade History", stats.get("trade_history", 0))
    c3.metric("🎓 Lessons Learned", stats.get("lessons_learned", 0))
    total = sum(stats.values())
    st.metric("Total Documents", total)

    st.markdown("---")

    # Available data files
    st.subheader("📁 Data Files on Disk")
    available = loader.list_available()
    for category, files in available.items():
        with st.expander(f"{category} ({len(files)} files)"):
            for f in files[:30]:
                st.text(f"  {f}")
            if len(files) > 30:
                st.text(f"  ... and {len(files) - 30} more")

    st.markdown("---")
    st.subheader("⚠️ Danger Zone")
    if st.button("🗑️ Clear ALL Knowledge Base Data", type="secondary"):
        st.warning("Are you sure? This will delete all RAG data.")
        if st.button("Yes, clear everything", type="primary"):
            rag.clear_all()
            st.success("Cleared!")
            st.rerun()

# ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "*Use this app to build the knowledge base before running analyses. "
    "The more context the KB Agent has, the better the trading decisions.*"
)

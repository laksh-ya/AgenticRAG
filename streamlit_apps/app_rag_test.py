"""
RAG Test App - Test RAG queries and KB Agent
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_rag.rag_manager import RAGManager
from agents.kb_agent import KnowledgeBaseAgent
from preferences import SUPPORTED_TICKERS

st.set_page_config(page_title="RAG Test", page_icon="🧠")

st.title("🧠 RAG & Knowledge Base Test")

# Initialize
@st.cache_resource
def get_rag():
    return RAGManager()

rag = get_rag()
kb = KnowledgeBaseAgent(rag)

# Tabs
tab1, tab2, tab3 = st.tabs(["Query", "Add Knowledge", "Stats"])

with tab1:
    st.header("Query Knowledge Base")
    
    col1, col2 = st.columns(2)
    with col1:
        ticker = st.selectbox("Ticker", SUPPORTED_TICKERS)
    with col2:
        store = st.selectbox("Store", ["All", "market_insights", "trade_history", "lessons_learned"])
    
    query = st.text_input("Query", f"Trading analysis for {ticker}")
    
    if st.button("Search"):
        with st.spinner("Searching..."):
            if store == "All":
                results = rag.query_all(query)
                for store_name, docs in results.items():
                    st.subheader(store_name)
                    for doc in docs:
                        st.text(doc["text"][:300])
                        st.divider()
            else:
                results = rag.query(store, query)
                for doc in results:
                    st.text(doc["text"][:300])
                    st.divider()
    
    st.subheader("KB Agent Pre-Query")
    if st.button("Run pre_query()"):
        result = kb.pre_query(ticker)
        st.json({
            "context": result["context"][:500],
            "lessons": result["lessons"],
            "decisions": result["decisions"]
        })

with tab2:
    st.header("Add Custom Knowledge")
    
    ticker = st.selectbox("Ticker", SUPPORTED_TICKERS, key="add_ticker")
    knowledge = st.text_area("Knowledge to add")
    
    if st.button("Add to KB"):
        kb.add_custom_knowledge(ticker, knowledge)
        st.success("Added!")

with tab3:
    st.header("Knowledge Base Stats")
    
    stats = rag.get_stats()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Market Insights", stats.get("market_insights", 0))
    col2.metric("Trade History", stats.get("trade_history", 0))
    col3.metric("Lessons Learned", stats.get("lessons_learned", 0))
    
    if st.button("Clear All", type="secondary"):
        rag.clear_all()
        st.warning("Cleared all knowledge!")
        st.rerun()

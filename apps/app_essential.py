"""
KARMA Essential Lab
Single app for View + Edit + Learn to test practical worth.
"""
import glob
import json
import os
import sys
from datetime import datetime

import streamlit as st

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from karma.agents.kb_agent import KnowledgeBaseAgent
from karma.config import CONFIG, PRESET_PORTFOLIOS, SUPPORTED_TICKERS
from karma.data.data_loader import DataLoader
from karma.graph.trading_graph import TradingGraph
from karma.rag.explainability import Explainability
from karma.rag.rag_manager import RAGManager


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _load_json(path: str):
    with open(path, "r") as f:
        return json.load(f)


def _save_json(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _list_result_files(results_dir: str):
    files = sorted(glob.glob(os.path.join(results_dir, "*.json")))
    return [p for p in files if not os.path.basename(p).startswith("_")]


def _evaluate(decision: str, ret_pct: float) -> bool:
    d = (decision or "HOLD").upper()
    if d == "BUY":
        return ret_pct > 0
    if d == "SELL":
        return ret_pct < 0
    return abs(ret_pct) <= 5.0


st.set_page_config(page_title="KARMA Essential Lab", page_icon="🧪", layout="wide")
st.title("🧪 KARMA Essential Lab")
st.caption("One place to run decisions, edit inputs, and teach outcomes.")

results_dir = CONFIG.get("results_dir", "./storage/results")
_ensure_dir(results_dir)
outcomes_file = os.path.join(results_dir, "_outcomes.json")

loader = DataLoader()
rag = RAGManager()
kb = KnowledgeBaseAgent(rag)
explainer = Explainability(rag)

# ---------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------
tab_view, tab_edit, tab_learn = st.tabs(["📈 View/Run", "🛠️ Edit", "🎓 Learn"])

# ---------------------------------------------------------------------
# View/Run
# ---------------------------------------------------------------------
with tab_view:
    st.subheader("Run Decision and Inspect Output")

    c1, c2, c3 = st.columns(3)
    with c1:
        ticker = st.selectbox("Ticker", SUPPORTED_TICKERS, key="view_ticker")
    with c2:
        run_date = st.date_input("Date", datetime.now(), key="view_date")
    with c3:
        preset_keys = list(PRESET_PORTFOLIOS.keys())
        preset = st.selectbox("Portfolio Preset", preset_keys, index=0, key="view_preset")

    if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
        tg = TradingGraph()
        with st.spinner("Running full pipeline..."):
            result = tg.run(
                ticker=ticker,
                date=run_date.strftime("%Y-%m-%d"),
                portfolio=PRESET_PORTFOLIOS[preset]["holdings"],
            )
            save_path = tg.save_result(result)

        st.success(f"Saved result: {save_path}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Decision", result.get("decision", "HOLD"))
        c2.metric("Confidence", f"{result.get('confidence', 0.0):.1%}")
        kb_stats = tg.get_kb_stats()
        c3.metric("KB Docs", sum(kb_stats.values()))

        st.text_area("Reasoning", result.get("reasoning", ""), height=260)
        if result.get("explainability_report"):
            with st.expander("Explainability Report"):
                st.text(result.get("explainability_report", ""))

    st.markdown("---")
    st.subheader("Browse Recent Results")

    result_files = _list_result_files(results_dir)
    if not result_files:
        st.info("No result files yet.")
    else:
        selected = st.selectbox(
            "Result File",
            options=result_files,
            format_func=lambda p: os.path.basename(p),
        )
        if st.button("Open Result"):
            data = _load_json(selected)
            st.json(data)

# ---------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------
with tab_edit:
    st.subheader("Edit Input Data and Knowledge")

    edit_tab_cache, edit_tab_kb = st.tabs(["📦 Cache JSON", "🧠 KB Notes"])

    with edit_tab_cache:
        c1, c2, c3 = st.columns(3)
        with c1:
            e_ticker = st.selectbox("Ticker", SUPPORTED_TICKERS, key="edit_ticker")
        with c2:
            e_type = st.selectbox("Data Type", ["fundamentals", "market", "news", "social"], key="edit_type")
        with c3:
            e_date = st.date_input("Date (for non-fundamentals)", datetime.now(), key="edit_date")

        payload = st.text_area(
            "Paste JSON to save into cache",
            height=220,
            placeholder='{"example": "value"}',
        )

        if st.button("💾 Save Cache JSON"):
            if not payload.strip():
                st.warning("Paste JSON first.")
            else:
                try:
                    obj = json.loads(payload)
                    save_date = e_date.strftime("%Y-%m-%d") if e_type != "fundamentals" else None
                    path = loader.save_json(e_ticker, e_type, obj, save_date)
                    st.success(f"Saved: {path}")
                except json.JSONDecodeError:
                    st.error("Invalid JSON.")

        st.markdown("---")
        st.caption("Current cached files")
        avail = loader.list_available()
        for subdir, files in avail.items():
            with st.expander(f"{subdir} ({len(files)})"):
                for f in files[:50]:
                    st.text(f)

    with edit_tab_kb:
        kb_ticker = st.selectbox("Ticker", SUPPORTED_TICKERS, key="kb_ticker")
        kb_text = st.text_area("Add a KB note / insight", height=180)
        if st.button("➕ Add KB Note"):
            if kb_text.strip():
                doc_id = kb.add_custom_knowledge(kb_ticker, kb_text.strip())
                st.success(f"Stored as KB doc: {doc_id}")
            else:
                st.warning("Write something first.")

        q = st.text_input("Query KB", "latest lessons")
        q_store = st.selectbox("Store", ["All", "market_insights", "trade_history", "lessons_learned"], key="q_store")
        if st.button("🔎 Query KB"):
            if q_store == "All":
                res = rag.query_all(q)
                if not res:
                    st.info("No matches.")
                for sn, docs in res.items():
                    with st.expander(f"{sn} ({len(docs)})"):
                        for d in docs:
                            st.text(d.get("text", "")[:500])
                            st.markdown("---")
            else:
                docs = rag.query(q_store, q)
                if not docs:
                    st.info("No matches.")
                for d in docs:
                    st.text(d.get("text", "")[:500])
                    st.markdown("---")

# ---------------------------------------------------------------------
# Learn
# ---------------------------------------------------------------------
with tab_learn:
    st.subheader("Teach System from T+1 Outcomes")

    result_files = _list_result_files(results_dir)
    if not result_files:
        st.info("No results available. Run at least one analysis first.")
    else:
        selected = st.selectbox(
            "Select Result",
            result_files,
            format_func=lambda p: os.path.basename(p),
            key="learn_select",
        )
        record = _load_json(selected)

        c1, c2, c3 = st.columns(3)
        c1.metric("Ticker", record.get("ticker", "-"))
        c2.metric("Decision", record.get("decision", "-"))
        c3.metric("Confidence", f"{float(record.get('confidence', 0.0)):.1%}")

        ret_pct = st.number_input(
            "Actual Next-Day Return (%)",
            min_value=-100.0,
            max_value=500.0,
            value=0.0,
            step=0.1,
        )

        if st.button("📚 Store Outcome Lesson", type="primary"):
            ticker = record.get("ticker", "")
            dt = record.get("date", datetime.now().strftime("%Y-%m-%d"))
            decision = record.get("decision", "HOLD")
            reasoning = record.get("reasoning", "")

            lesson_id = explainer.learn_from_outcome(
                ticker=ticker,
                date=dt,
                decision=decision,
                reasoning=reasoning,
                actual_return=ret_pct / 100.0,
            )

            # Keep simple outcomes ledger for quick metrics.
            outcomes = {}
            if os.path.exists(outcomes_file):
                try:
                    outcomes = _load_json(outcomes_file)
                except Exception:
                    outcomes = {}

            correct = _evaluate(decision, ret_pct)
            outcomes[f"{ticker}_{dt}"] = {
                "return_pct": ret_pct / 100.0,
                "was_correct": correct,
                "logged_at": datetime.now().isoformat(),
                "decision": decision,
            }
            _save_json(outcomes_file, outcomes)

            if correct:
                st.success(f"Correct decision. Lesson stored: {lesson_id}")
            else:
                st.warning(f"Wrong decision. Lesson stored: {lesson_id}")

    st.markdown("---")
    stats = rag.get_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("Market Insights", stats.get("market_insights", 0))
    c2.metric("Trade History", stats.get("trade_history", 0))
    c3.metric("Lessons Learned", stats.get("lessons_learned", 0))

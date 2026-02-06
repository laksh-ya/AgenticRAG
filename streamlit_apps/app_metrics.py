"""
Metrics & Evaluation Dashboard — Track decisions, log outcomes, measure performance.

Tabs:
  1. Decision Log      — every analysis result in one table, with outcome entry
  2. Log Outcome       — enter actual return for a past decision, system learns
  3. Performance        — win rate, confidence calibration, per-ticker stats
  4. Charts            — confidence vs return scatter, cumulative P&L, decision dist
  5. Lessons           — browse what the system has learned so far
"""
import streamlit as st
import sys
import os
import json
import glob
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_rag.explainability import Explainability
from multi_rag.rag_manager import RAGManager
from agents.kb_agent import KnowledgeBaseAgent
from preferences import SUPPORTED_TICKERS, CONFIG

st.set_page_config(page_title="Metrics & Evaluation", page_icon="📊", layout="wide")
st.title("📊 Metrics & Evaluation Dashboard")

# ═══════════════════════════════════════════════════════════════════════════
#  Shared state — load results + outcomes
# ═══════════════════════════════════════════════════════════════════════════

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
OUTCOMES_FILE = os.path.join(RESULTS_DIR, "_outcomes.json")

# RAG setup for learning
rag = RAGManager()
explainer = Explainability(rag)


def _load_all_results() -> List[Dict]:
    """Load every result JSON from results/ directory."""
    results = []
    pattern = os.path.join(RESULTS_DIR, "*.json")
    for path in sorted(glob.glob(pattern)):
        filename = os.path.basename(path)
        if filename.startswith("_"):
            continue  # skip meta files like _outcomes.json
        try:
            with open(path) as f:
                data = json.load(f)
            data["_file"] = filename
            results.append(data)
        except Exception:
            continue
    return results


def _load_outcomes() -> Dict[str, Dict]:
    """Load outcomes log. Key = 'TICKER_DATE', value = {return_pct, logged_at, was_correct}."""
    if os.path.exists(OUTCOMES_FILE):
        with open(OUTCOMES_FILE) as f:
            return json.load(f)
    return {}


def _save_outcomes(outcomes: Dict):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(OUTCOMES_FILE, "w") as f:
        json.dump(outcomes, f, indent=2)


def _merge_results_outcomes(results: List[Dict], outcomes: Dict) -> List[Dict]:
    """Merge results with their outcome data."""
    merged = []
    for r in results:
        key = f"{r['ticker']}_{r['date']}"
        entry = {
            "ticker": r.get("ticker", ""),
            "date": r.get("date", ""),
            "decision": r.get("decision", ""),
            "confidence": r.get("confidence", 0),
            "reasoning_preview": r.get("reasoning", "")[:150] + "…" if r.get("reasoning") else "",
            "_file": r.get("_file", ""),
        }
        outcome = outcomes.get(key)
        if outcome:
            entry["actual_return"] = outcome["return_pct"]
            entry["was_correct"] = outcome["was_correct"]
            entry["outcome_logged"] = outcome.get("logged_at", "")
        else:
            entry["actual_return"] = None
            entry["was_correct"] = None
            entry["outcome_logged"] = None
        merged.append(entry)
    return merged


# Load everything
all_results = _load_all_results()
outcomes = _load_outcomes()
merged = _merge_results_outcomes(all_results, outcomes)

# ═══════════════════════════════════════════════════════════════════════════
#  Tabs
# ═══════════════════════════════════════════════════════════════════════════
tab_log, tab_outcome, tab_perf, tab_charts, tab_lessons = st.tabs(
    ["📋 Decision Log", "🎯 Log Outcome", "📈 Performance", "📉 Charts", "🧠 Lessons"]
)

# ─────────────────────────────────────────────────────────────────────────
#  Tab 1 — Decision Log
# ─────────────────────────────────────────────────────────────────────────
with tab_log:
    st.subheader("All Analysis Decisions")

    if not merged:
        st.info("No results yet. Run an analysis from the main app first.")
    else:
        # Summary metrics
        total = len(merged)
        with_outcomes = [m for m in merged if m["actual_return"] is not None]
        pending = total - len(with_outcomes)

        cols = st.columns(4)
        cols[0].metric("Total Analyses", total)
        cols[1].metric("Outcomes Logged", len(with_outcomes))
        cols[2].metric("Pending Outcomes", pending)
        cols[3].metric("Tickers Analyzed", len(set(m["ticker"] for m in merged)))

        st.markdown("---")

        # Build display table
        table_data = []
        for m in merged:
            status = ""
            if m["was_correct"] is True:
                status = "✅ Correct"
            elif m["was_correct"] is False:
                status = "❌ Wrong"
            else:
                status = "⏳ Pending"

            ret_str = f"{m['actual_return']:+.1%}" if m["actual_return"] is not None else "—"

            table_data.append({
                "Ticker": m["ticker"],
                "Date": m["date"],
                "Decision": m["decision"],
                "Confidence": f"{m['confidence']:.0%}",
                "Actual Return": ret_str,
                "Result": status,
            })

        st.dataframe(table_data, use_container_width=True)

        # Expandable reasoning for each
        st.markdown("---")
        st.subheader("📝 Decision Details")
        for m in merged:
            label = f"{m['ticker']} ({m['date']}) — {m['decision']}"
            if m["was_correct"] is True:
                label = f"✅ {label}"
            elif m["was_correct"] is False:
                label = f"❌ {label}"
            else:
                label = f"⏳ {label}"

            with st.expander(label, expanded=False):
                st.markdown(f"**Confidence:** {m['confidence']:.0%}")
                if m["actual_return"] is not None:
                    st.markdown(f"**Actual Return:** {m['actual_return']:+.1%}")
                st.text_area(
                    "Reasoning",
                    m["reasoning_preview"],
                    height=100,
                    disabled=True,
                    key=f"reason_{m['_file']}",
                )


# ─────────────────────────────────────────────────────────────────────────
#  Tab 2 — Log Outcome
# ─────────────────────────────────────────────────────────────────────────
with tab_outcome:
    st.subheader("🎯 Log Actual Outcome for a Past Decision")
    st.caption(
        "After N days, come back here and enter what actually happened. "
        "The system will learn from it and use those lessons in future analyses."
    )

    # Filter to results without outcomes
    pending_results = [m for m in merged if m["actual_return"] is None]

    if not pending_results:
        if not merged:
            st.info("No results yet — run an analysis first.")
        else:
            st.success("🎉 All decisions have outcomes logged! Check the Performance tab.")
    else:
        # Pick which decision to evaluate
        options = [f"{m['ticker']}  |  {m['date']}  |  {m['decision']}" for m in pending_results]
        selected_idx = st.selectbox("Select decision to evaluate", range(len(options)), format_func=lambda i: options[i])
        selected = pending_results[selected_idx]

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Ticker:** {selected['ticker']}")
            st.markdown(f"**Date:** {selected['date']}")
            st.markdown(f"**Decision:** {selected['decision']}")
            st.markdown(f"**Confidence:** {selected['confidence']:.0%}")
        with col2:
            actual_return_pct = st.number_input(
                "Actual Return (%)",
                min_value=-100.0,
                max_value=500.0,
                value=0.0,
                step=0.1,
                help="e.g., 5.0 means the stock went up +5%",
            )

        # Load full reasoning from file for the learning call
        result_path = os.path.join(RESULTS_DIR, selected["_file"])
        full_reasoning = ""
        try:
            with open(result_path) as f:
                full_data = json.load(f)
            full_reasoning = full_data.get("reasoning", "")
        except Exception:
            pass

        if st.button("📚 Log Outcome & Teach System", type="primary", use_container_width=True):
            actual_decimal = actual_return_pct / 100.0
            decision = selected["decision"]

            # Determine correctness
            if decision == "BUY":
                was_correct = actual_decimal > 0
            elif decision == "SELL":
                was_correct = actual_decimal < 0
            else:
                was_correct = abs(actual_decimal) < 0.05

            # 1. Save to outcomes file
            key = f"{selected['ticker']}_{selected['date']}"
            outcomes[key] = {
                "return_pct": actual_decimal,
                "was_correct": was_correct,
                "logged_at": datetime.now().isoformat(),
                "decision": decision,
            }
            _save_outcomes(outcomes)

            # 2. Teach the RAG system
            try:
                lesson_id = explainer.learn_from_outcome(
                    ticker=selected["ticker"],
                    date=selected["date"],
                    decision=decision,
                    reasoning=full_reasoning,
                    actual_return=actual_decimal,
                )
                rag_status = f"Lesson stored in RAG (ID: {lesson_id})"
            except Exception as e:
                rag_status = f"RAG learning failed: {e}"

            # 3. Show result
            if was_correct:
                st.balloons()
                st.success(f"✅ {decision} was CORRECT! Return: {actual_return_pct:+.1f}%")
            else:
                st.error(f"❌ {decision} was WRONG. Return: {actual_return_pct:+.1f}%")

            st.caption(rag_status)
            st.info("The system has learned from this outcome. Future analyses will be smarter.")
            st.rerun()

    # Bulk entry
    st.markdown("---")
    st.subheader("⚡ Quick Bulk Entry")
    st.caption("Rapidly log outcomes for multiple decisions at once.")

    for m in pending_results[:10]:
        col_t, col_d, col_dec, col_ret, col_btn = st.columns([1, 1.5, 1, 1.5, 1])
        with col_t:
            st.markdown(f"**{m['ticker']}**")
        with col_d:
            st.caption(m['date'])
        with col_dec:
            st.caption(m['decision'])
        with col_ret:
            ret = st.number_input(
                "Return %",
                min_value=-100.0, max_value=500.0, value=0.0, step=0.1,
                key=f"bulk_{m['_file']}",
                label_visibility="collapsed",
            )
        with col_btn:
            if st.button("Log", key=f"bulkbtn_{m['_file']}"):
                decimal = ret / 100.0
                d = m["decision"]
                if d == "BUY":
                    correct = decimal > 0
                elif d == "SELL":
                    correct = decimal < 0
                else:
                    correct = abs(decimal) < 0.05

                key = f"{m['ticker']}_{m['date']}"
                outcomes[key] = {
                    "return_pct": decimal,
                    "was_correct": correct,
                    "logged_at": datetime.now().isoformat(),
                    "decision": d,
                }
                _save_outcomes(outcomes)

                try:
                    result_path = os.path.join(RESULTS_DIR, m["_file"])
                    with open(result_path) as f:
                        fd = json.load(f)
                    explainer.learn_from_outcome(
                        ticker=m["ticker"], date=m["date"],
                        decision=d, reasoning=fd.get("reasoning", ""),
                        actual_return=decimal,
                    )
                except Exception:
                    pass
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────
#  Tab 3 — Performance Metrics
# ─────────────────────────────────────────────────────────────────────────
with tab_perf:
    st.subheader("📈 Performance Metrics")

    evaluated = [m for m in merged if m["actual_return"] is not None]

    if not evaluated:
        st.info(
            "No outcomes logged yet. Run analyses, wait for results, "
            "then log actual returns in the **Log Outcome** tab."
        )
    else:
        # Overall metrics
        total_eval = len(evaluated)
        correct = sum(1 for m in evaluated if m["was_correct"])
        wrong = total_eval - correct
        win_rate = correct / total_eval if total_eval > 0 else 0
        avg_confidence = sum(m["confidence"] for m in evaluated) / total_eval
        avg_return = sum(m["actual_return"] for m in evaluated) / total_eval

        # Confidence when right vs wrong
        correct_entries = [m for m in evaluated if m["was_correct"]]
        wrong_entries = [m for m in evaluated if not m["was_correct"]]
        avg_conf_right = sum(m["confidence"] for m in correct_entries) / len(correct_entries) if correct_entries else 0
        avg_conf_wrong = sum(m["confidence"] for m in wrong_entries) / len(wrong_entries) if wrong_entries else 0

        st.markdown("### Overall")
        cols = st.columns(5)
        cols[0].metric("Win Rate", f"{win_rate:.0%}", f"{correct}W / {wrong}L")
        cols[1].metric("Avg Return", f"{avg_return:+.2%}")
        cols[2].metric("Avg Confidence", f"{avg_confidence:.0%}")
        cols[3].metric("Conf (When Right)", f"{avg_conf_right:.0%}")
        cols[4].metric("Conf (When Wrong)", f"{avg_conf_wrong:.0%}")

        # Per-ticker breakdown
        st.markdown("---")
        st.markdown("### Per-Ticker Breakdown")

        tickers_seen = sorted(set(m["ticker"] for m in evaluated))
        ticker_rows = []
        for t in tickers_seen:
            t_entries = [m for m in evaluated if m["ticker"] == t]
            t_correct = sum(1 for m in t_entries if m["was_correct"])
            t_total = len(t_entries)
            t_win = t_correct / t_total if t_total > 0 else 0
            t_avg_ret = sum(m["actual_return"] for m in t_entries) / t_total
            t_avg_conf = sum(m["confidence"] for m in t_entries) / t_total
            ticker_rows.append({
                "Ticker": t,
                "Analyses": t_total,
                "Win Rate": f"{t_win:.0%}",
                "Avg Return": f"{t_avg_ret:+.2%}",
                "Avg Confidence": f"{t_avg_conf:.0%}",
                "Record": f"{t_correct}W / {t_total - t_correct}L",
            })
        st.dataframe(ticker_rows, use_container_width=True)

        # Per-decision type
        st.markdown("---")
        st.markdown("### By Decision Type")
        for dec_type in ["BUY", "SELL", "HOLD"]:
            entries = [m for m in evaluated if m["decision"] == dec_type]
            if not entries:
                continue
            dec_correct = sum(1 for m in entries if m["was_correct"])
            dec_total = len(entries)
            dec_win = dec_correct / dec_total if dec_total > 0 else 0
            dec_avg_ret = sum(m["actual_return"] for m in entries) / dec_total
            st.markdown(
                f"**{dec_type}**: {dec_total} times, "
                f"Win Rate: {dec_win:.0%}, "
                f"Avg Return: {dec_avg_ret:+.2%}, "
                f"Record: {dec_correct}W / {dec_total - dec_correct}L"
            )

        # Best & Worst
        st.markdown("---")
        cols = st.columns(2)
        with cols[0]:
            st.markdown("### 🏆 Best Calls")
            best = sorted(evaluated, key=lambda m: m["actual_return"], reverse=True)[:5]
            for m in best:
                icon = "✅" if m["was_correct"] else "❌"
                st.markdown(
                    f"{icon} **{m['ticker']}** ({m['date']}) — "
                    f"{m['decision']} → {m['actual_return']:+.1%}"
                )
        with cols[1]:
            st.markdown("### 💀 Worst Calls")
            worst = sorted(evaluated, key=lambda m: m["actual_return"])[:5]
            for m in worst:
                icon = "✅" if m["was_correct"] else "❌"
                st.markdown(
                    f"{icon} **{m['ticker']}** ({m['date']}) — "
                    f"{m['decision']} → {m['actual_return']:+.1%}"
                )


# ─────────────────────────────────────────────────────────────────────────
#  Tab 4 — Charts
# ─────────────────────────────────────────────────────────────────────────
with tab_charts:
    st.subheader("📉 Visual Analytics")

    evaluated = [m for m in merged if m["actual_return"] is not None]

    if not evaluated:
        st.info("Log some outcomes first to see charts.")
    else:
        import pandas as pd

        df = pd.DataFrame(evaluated)
        df["actual_return_pct"] = df["actual_return"] * 100
        df["confidence_pct"] = df["confidence"] * 100

        # Decision distribution (always available)
        st.markdown("### Decision Distribution (All Analyses)")
        all_df = pd.DataFrame(merged)
        dec_counts = all_df["decision"].value_counts()
        st.bar_chart(dec_counts)

        # Confidence vs Return scatter
        st.markdown("### Confidence vs Actual Return")
        scatter_df = df[["confidence_pct", "actual_return_pct", "ticker", "decision"]].copy()
        scatter_df.columns = ["Confidence (%)", "Actual Return (%)", "Ticker", "Decision"]
        st.scatter_chart(
            scatter_df,
            x="Confidence (%)",
            y="Actual Return (%)",
            color="Ticker",
        )

        # Win rate over time
        st.markdown("### Cumulative Win Rate Over Time")
        df_sorted = df.sort_values("date")
        cum_correct = 0
        cum_total = 0
        win_over_time = []
        for _, row in df_sorted.iterrows():
            cum_total += 1
            if row["was_correct"]:
                cum_correct += 1
            win_over_time.append({
                "Date": row["date"],
                "Win Rate (%)": round(cum_correct / cum_total * 100, 1),
            })
        win_df = pd.DataFrame(win_over_time)
        if not win_df.empty:
            st.line_chart(win_df.set_index("Date"))

        # Cumulative P&L
        st.markdown("### Cumulative P&L (if you followed every signal)")
        df_sorted = df.sort_values("date")
        cumulative = 0
        pnl_data = []
        for _, row in df_sorted.iterrows():
            ret = row["actual_return"]
            dec = row["decision"]
            # BUY = long exposure, SELL = short exposure, HOLD = no exposure
            if dec == "BUY":
                cumulative += ret
            elif dec == "SELL":
                cumulative -= ret  # profit on short if price drops
            # HOLD = no P&L
            pnl_data.append({
                "Date": row["date"],
                "Cumulative Return (%)": round(cumulative * 100, 2),
            })
        pnl_df = pd.DataFrame(pnl_data)
        if not pnl_df.empty:
            st.line_chart(pnl_df.set_index("Date"))

        # Return distribution
        st.markdown("### Return Distribution")
        st.bar_chart(df["actual_return_pct"].value_counts().sort_index())


# ─────────────────────────────────────────────────────────────────────────
#  Tab 5 — Lessons (what the system has learned)
# ─────────────────────────────────────────────────────────────────────────
with tab_lessons:
    st.subheader("🧠 Lessons Learned by the System")
    st.caption(
        "These lessons are stored in ChromaDB and retrieved by the KB Agent "
        "during future analyses to avoid repeating mistakes."
    )

    # Query lessons from RAG
    try:
        stats = rag.get_stats()
        lesson_count = stats.get("lessons_learned", 0)
        st.metric("Total Lessons Stored", lesson_count)

        if lesson_count > 0:
            st.markdown("---")
            # Query lessons for each ticker
            for ticker in SUPPORTED_TICKERS:
                results = rag.query_all(f"Lessons learned for {ticker}", n_per_store=5)
                lessons = results.get("lessons_learned", [])
                if lessons:
                    with st.expander(f"📖 {ticker} — {len(lessons)} lessons", expanded=False):
                        for i, r in enumerate(lessons):
                            st.markdown(f"**Lesson {i+1}:**")
                            st.text(r.get("text", str(r))[:500])
                            meta = r.get("metadata", {})
                            if meta:
                                cols = st.columns(3)
                                if meta.get("date"):
                                    cols[0].caption(f"📅 {meta['date']}")
                                if meta.get("was_correct") is not None:
                                    icon = "✅" if meta["was_correct"] else "❌"
                                    cols[1].caption(f"{icon} {'Correct' if meta['was_correct'] else 'Wrong'}")
                                if meta.get("actual_return") is not None:
                                    cols[2].caption(f"📊 Return: {meta['actual_return']:+.2%}")
                            st.markdown("---")
        else:
            st.info(
                "No lessons yet. Log outcomes in the **Log Outcome** tab — "
                "the system will generate lessons automatically."
            )
    except Exception as e:
        st.error(f"Could not query lessons: {e}")

# ──────────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "*Run analyses → Wait for results → Log outcomes here → "
    "System learns → Future decisions get smarter. That's the Agentic RAG loop.*"
)

"""
KARMA Master 5-Day Evaluation App
Single-brain evaluation dashboard with KB mode switching (Collection -> Learning).
"""
import os
import sys
from datetime import date, timedelta
from typing import Dict, List

import pandas as pd
import streamlit as st

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from karma.config import SUPPORTED_TICKERS
from karma.graph.trading_graph import TradingGraph
from karma.rag.rag_manager import RAGManager


STARTING_CAPITAL = 10000.0
TRADE_SIZE = 2000.0
MAX_TRADES_PER_DAY = 3
MAX_DAILY_EXPOSURE = 6000.0


def day_mode(day_num: int) -> str:
    return "Collection" if day_num <= 2 else "Learning"


def evaluate_correctness(decision: str, ret_pct: float) -> bool:
    d = (decision or "HOLD").upper()
    if d == "BUY":
        return ret_pct > 0
    if d == "SELL":
        return ret_pct < 0
    return abs(ret_pct) <= 5.0


def lesson_text(decision: str, ret_pct: float, correct: bool) -> str:
    if correct:
        return (
            f"{decision} was correct at {ret_pct:+.2f}% next-day move. "
            "Reinforce this signal pattern in similar setups."
        )
    return (
        f"{decision} was wrong at {ret_pct:+.2f}% next-day move. "
        "Review signal weighting and avoid repeating this setup without stronger confirmation."
    )


def init_state():
    if "master_eval" not in st.session_state:
        st.session_state["master_eval"] = {
            "days": {},
            "start_date": date.today(),
            "tickers": ["AAPL", "GOOGL", "AMZN"],
        }


def run_day(tickers: List[str], eval_date: str, day_num: int) -> List[Dict]:
    """
    Run one evaluation day.
    Day 1-2 (Collection): temporarily disable KB retrieval + storage during decision pass.
    Day 3-5 (Learning): normal TradingGraph behavior.
    """
    tg = TradingGraph()
    results: List[Dict] = []

    kb_enabled = day_num >= 3

    # Monkey patch KB behavior during decision run for strict collection-mode gating.
    if not kb_enabled:
        original_pre = tg.kb_agent.pre_query
        original_post = tg.kb_agent.post_learn

        def _empty_pre_query(_ticker: str, _date: str = None):
            return {"context": "", "lessons": [], "decisions": [], "raw": {}}

        def _noop_post_learn(*_args, **_kwargs):
            return {"decision_id": None, "insight_ids": []}

        tg.kb_agent.pre_query = _empty_pre_query
        tg.kb_agent.post_learn = _noop_post_learn

    try:
        for tk in tickers:
            out = tg.run(tk, eval_date, portfolio=[])
            results.append(
                {
                    "ticker": tk,
                    "day": day_num,
                    "decision": out.get("decision", "HOLD"),
                    "confidence": float(out.get("confidence", 0.5)),
                    "reasoning": out.get("reasoning", ""),
                    "mode": day_mode(day_num),
                    "evaluated": False,
                    "return_pct": None,
                    "correct": None,
                }
            )
    finally:
        if not kb_enabled:
            tg.kb_agent.pre_query = original_pre
            tg.kb_agent.post_learn = original_post

    # Enforce max 3 trades/day and fixed sizing by confidence ranking.
    active = [r for r in results if r["decision"] in ("BUY", "SELL")]
    active_sorted = sorted(active, key=lambda x: x["confidence"], reverse=True)
    allowed = {r["ticker"] for r in active_sorted[:MAX_TRADES_PER_DAY]}

    for r in results:
        if r["decision"] in ("BUY", "SELL") and r["ticker"] not in allowed:
            r["decision"] = "HOLD"
            r["reasoning"] = (
                "Trade converted to HOLD due to daily risk cap "
                f"({MAX_TRADES_PER_DAY} trades / ${MAX_DAILY_EXPOSURE:.0f} max exposure)."
            )

    return results


def daily_table(data: Dict) -> pd.DataFrame:
    rows = []
    for d in range(1, 6):
        day_data = data.get("days", {}).get(str(d), {})
        entries = day_data.get("entries", [])
        if not entries:
            rows.append(
                {
                    "Day": d,
                    "Mode": day_mode(d),
                    "Trades": 0,
                    "Win Rate": None,
                    "Avg Return %": None,
                    "HOLD %": None,
                    "Avg Confidence": None,
                }
            )
            continue

        trades = sum(1 for e in entries if e["decision"] in ("BUY", "SELL"))
        holds = sum(1 for e in entries if e["decision"] == "HOLD")
        evaled = [e for e in entries if e["evaluated"]]
        win = None
        avg_ret = None
        if evaled:
            win = sum(1 for e in evaled if e["correct"]) / len(evaled)
            avg_ret = sum(float(e["return_pct"]) for e in evaled) / len(evaled)

        rows.append(
            {
                "Day": d,
                "Mode": day_mode(d),
                "Trades": trades,
                "Win Rate": win,
                "Avg Return %": avg_ret,
                "HOLD %": holds / len(entries),
                "Avg Confidence": sum(e["confidence"] for e in entries) / len(entries),
            }
        )

    return pd.DataFrame(rows)


def phase_slice(df: pd.DataFrame, days: List[int]) -> Dict:
    part = df[df["Day"].isin(days)]
    out = {
        "Win Rate": part["Win Rate"].dropna().mean() if not part["Win Rate"].dropna().empty else None,
        "Avg Return %": part["Avg Return %"].dropna().mean() if not part["Avg Return %"].dropna().empty else None,
        "HOLD %": part["HOLD %"].dropna().mean() if not part["HOLD %"].dropna().empty else None,
        "Avg Confidence": part["Avg Confidence"].dropna().mean() if not part["Avg Confidence"].dropna().empty else None,
    }
    return out


def fmt_pct(v):
    if v is None or pd.isna(v):
        return "-"
    return f"{v:.1%}"


def fmt_ret(v):
    if v is None or pd.isna(v):
        return "-"
    return f"{v:+.2f}%"


st.set_page_config(page_title="Master 5-Day Eval", page_icon="🧠", layout="wide")
st.title("🧠 Master 5-Day Adaptive Evaluation")
st.caption("Single brain mode with Day 1-2 Collection and Day 3-5 Learning.")

init_state()
state = st.session_state["master_eval"]

c1, c2, c3 = st.columns(3)
with c1:
    start_date = st.date_input("Start Date", value=state.get("start_date", date.today()))
with c2:
    tickers = st.multiselect("Tickers", SUPPORTED_TICKERS, default=state.get("tickers", ["AAPL", "GOOGL", "AMZN"]))
with c3:
    day_num = st.selectbox("Evaluation Day", [1, 2, 3, 4, 5], index=0)

state["start_date"] = start_date
state["tickers"] = tickers

curr_date = start_date + timedelta(days=day_num - 1)
mode = day_mode(day_num)

st.info(
    f"Day {day_num}: KB Mode = {mode} | Trade Size = ${TRADE_SIZE:.0f} | "
    f"Max Trades/Day = {MAX_TRADES_PER_DAY} | Max Exposure = ${MAX_DAILY_EXPOSURE:.0f}"
)

if st.button("Run Day Analysis", type="primary", use_container_width=True):
    if not tickers:
        st.warning("Select at least one ticker.")
    else:
        with st.spinner(f"Running Day {day_num} for {curr_date.isoformat()}..."):
            entries = run_day(tickers, curr_date.isoformat(), day_num)
            state["days"][str(day_num)] = {
                "date": curr_date.isoformat(),
                "mode": mode,
                "entries": entries,
            }
        st.success("Day run complete.")

st.markdown("---")

# Day outputs
st.subheader("Decision Output")
day_data = state.get("days", {}).get(str(day_num))
if not day_data:
    st.caption("No run recorded for this day yet.")
else:
    entries = day_data["entries"]
    used_capital = sum(TRADE_SIZE for e in entries if e["decision"] in ("BUY", "SELL"))
    st.metric("Capital Used Today", f"${used_capital:,.0f}")

    for e in entries:
        with st.expander(f"{e['ticker']} | {e['decision']} | conf {e['confidence']:.2f}", expanded=False):
            st.write(f"Mode: {e['mode']}")
            st.write("Reasoning:")
            st.write(e["reasoning"] or "-")

# Outcome logging
st.markdown("---")
st.subheader("T+1 Outcome Logging")
if day_data:
    entries = day_data["entries"]
    for i, e in enumerate(entries):
        cols = st.columns([1.1, 1, 1.5, 1])
        cols[0].write(f"{e['ticker']} ({e['decision']})")
        ret = cols[1].number_input(
            "Return %",
            min_value=-100.0,
            max_value=500.0,
            value=0.0 if e["return_pct"] is None else float(e["return_pct"]),
            step=0.1,
            key=f"ret_{day_num}_{i}",
            label_visibility="collapsed",
        )
        if cols[2].button("Evaluate", key=f"eval_{day_num}_{i}"):
            correct = evaluate_correctness(e["decision"], ret)
            e["return_pct"] = ret
            e["correct"] = correct
            e["evaluated"] = True

            # Persist outcome in KB as explicit lessons.
            rag = RAGManager()
            rag.store_decision(
                ticker=e["ticker"],
                date=day_data["date"],
                decision=e["decision"],
                reasoning=e["reasoning"],
                confidence=e["confidence"],
            )
            rag.store_lesson(
                ticker=e["ticker"],
                date=day_data["date"],
                lesson=lesson_text(e["decision"], ret, correct),
                was_correct=correct,
                actual_return=ret / 100.0,
            )
            st.success(f"Stored outcome for {e['ticker']}.")

        badge = "✅" if e["correct"] is True else ("❌" if e["correct"] is False else "⏳")
        cols[3].write(badge)

st.markdown("---")

# Tables section
st.subheader("Results Tables")
df = daily_table(state)
show_df = df.copy()
show_df["Win Rate"] = show_df["Win Rate"].apply(fmt_pct)
show_df["Avg Return %"] = show_df["Avg Return %"].apply(fmt_ret)
show_df["HOLD %"] = show_df["HOLD %"].apply(fmt_pct)
show_df["Avg Confidence"] = show_df["Avg Confidence"].apply(lambda x: "-" if pd.isna(x) else f"{x:.2f}")
st.markdown("Table 1 - Daily Performance Progression")
st.dataframe(show_df, use_container_width=True)

p12 = phase_slice(df, [1, 2])
p35 = phase_slice(df, [3, 4, 5])

improve = {
    "Win Rate": None if p12["Win Rate"] is None or p35["Win Rate"] is None else p35["Win Rate"] - p12["Win Rate"],
    "Avg Return %": None if p12["Avg Return %"] is None or p35["Avg Return %"] is None else p35["Avg Return %"] - p12["Avg Return %"],
    "HOLD %": None if p12["HOLD %"] is None or p35["HOLD %"] is None else p35["HOLD %"] - p12["HOLD %"],
    "Avg Confidence": None if p12["Avg Confidence"] is None or p35["Avg Confidence"] is None else p35["Avg Confidence"] - p12["Avg Confidence"],
}

phase_tbl = pd.DataFrame(
    [
        {
            "Metric": "Win Rate",
            "Day 1-2 (No KB)": fmt_pct(p12["Win Rate"]),
            "Day 3-5 (KB Active)": fmt_pct(p35["Win Rate"]),
            "Improvement": fmt_pct(improve["Win Rate"]),
        },
        {
            "Metric": "Avg Return",
            "Day 1-2 (No KB)": fmt_ret(p12["Avg Return %"]),
            "Day 3-5 (KB Active)": fmt_ret(p35["Avg Return %"]),
            "Improvement": fmt_ret(improve["Avg Return %"]),
        },
        {
            "Metric": "HOLD Decisions",
            "Day 1-2 (No KB)": fmt_pct(p12["HOLD %"]),
            "Day 3-5 (KB Active)": fmt_pct(p35["HOLD %"]),
            "Improvement": fmt_pct(improve["HOLD %"]),
        },
        {
            "Metric": "Avg Confidence",
            "Day 1-2 (No KB)": "-" if p12["Avg Confidence"] is None else f"{p12['Avg Confidence']:.2f}",
            "Day 3-5 (KB Active)": "-" if p35["Avg Confidence"] is None else f"{p35['Avg Confidence']:.2f}",
            "Improvement": "-" if improve["Avg Confidence"] is None else f"{improve['Avg Confidence']:+.2f}",
        },
    ]
)

st.markdown("Table 2 - Phase-wise Comparison")
st.dataframe(phase_tbl, use_container_width=True)

# Portfolio simulation and baseline
all_entries = []
for d in state.get("days", {}).values():
    all_entries.extend(d.get("entries", []))

evaled = [e for e in all_entries if e.get("evaluated")]
trade_evaled = [e for e in evaled if e["decision"] in ("BUY", "SELL")]

pnl = 0.0
for e in trade_evaled:
    ret = float(e["return_pct"]) / 100.0
    if e["decision"] == "BUY":
        pnl += TRADE_SIZE * ret
    elif e["decision"] == "SELL":
        pnl += TRADE_SIZE * (-ret)

final_cap = STARTING_CAPITAL + pnl
port_tbl = pd.DataFrame(
    [
        {"Metric": "Initial Capital", "Value": f"${STARTING_CAPITAL:,.0f}"},
        {"Metric": "Final Capital", "Value": f"${final_cap:,.0f}"},
        {"Metric": "Total Return", "Value": f"{(pnl / STARTING_CAPITAL):+.2%}"},
        {"Metric": "Total Trades", "Value": str(len(trade_evaled))},
        {"Metric": "Profitable Trades", "Value": str(sum(1 for e in trade_evaled if e["correct"]))},
        {"Metric": "Losing Trades", "Value": str(sum(1 for e in trade_evaled if e["correct"] is False))},
    ]
)
st.markdown("Table 3 - Portfolio Simulation")
st.dataframe(port_tbl, use_container_width=True)

if evaled:
    always_buy_win = sum(1 for e in evaled if float(e["return_pct"]) > 0) / len(evaled)
    always_buy_avg = sum(float(e["return_pct"]) for e in evaled) / len(evaled)
    always_buy_total = (TRADE_SIZE * len(evaled) * (always_buy_avg / 100.0)) / STARTING_CAPITAL

    agent_win = sum(1 for e in trade_evaled if e["correct"]) / len(trade_evaled) if trade_evaled else 0.0
    agent_avg = sum(float(e["return_pct"]) for e in trade_evaled) / len(trade_evaled) if trade_evaled else 0.0
    agent_total = (pnl / STARTING_CAPITAL) if STARTING_CAPITAL else 0.0

    base_tbl = pd.DataFrame(
        [
            {
                "Strategy": "Always BUY",
                "Win Rate": f"{always_buy_win:.1%}",
                "Avg Return": f"{always_buy_avg:+.2f}%",
                "Total Return": f"{always_buy_total:+.2%}",
            },
            {
                "Strategy": "AgenticRAG",
                "Win Rate": f"{agent_win:.1%}",
                "Avg Return": f"{agent_avg:+.2f}%",
                "Total Return": f"{agent_total:+.2%}",
            },
        ]
    )
    st.markdown("Table 4 - Baseline Comparison")
    st.dataframe(base_tbl, use_container_width=True)

early = [e for e in evaled if e.get("day") in [1, 2]]
late = [e for e in evaled if e.get("day") in [4, 5]]

if early or late:
    kb_tbl = pd.DataFrame(
        [
            {
                "Metric": "Win Rate",
                "Early (Day 1-2)": "-" if not early else f"{(sum(1 for e in early if e['correct']) / len(early)):.1%}",
                "Late (Day 4-5)": "-" if not late else f"{(sum(1 for e in late if e['correct']) / len(late)):.1%}",
            },
            {
                "Metric": "HOLD Decisions",
                "Early (Day 1-2)": "-" if not early else f"{(sum(1 for e in early if e['decision'] == 'HOLD') / len(early)):.1%}",
                "Late (Day 4-5)": "-" if not late else f"{(sum(1 for e in late if e['decision'] == 'HOLD') / len(late)):.1%}",
            },
            {
                "Metric": "Confidence",
                "Early (Day 1-2)": "-" if not early else f"{(sum(e['confidence'] for e in early) / len(early)):.2f}",
                "Late (Day 4-5)": "-" if not late else f"{(sum(e['confidence'] for e in late) / len(late)):.2f}",
            },
        ]
    )
    st.markdown("Table 5 - KB Learning Effect")
    st.dataframe(kb_tbl, use_container_width=True)

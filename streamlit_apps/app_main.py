"""
Main Streamlit App - Full Trading Workflow with Live Agent Reasoning.
Inspired by TradingAgents CLI: shows each agent step as it runs.
"""
import streamlit as st
import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from graphs.trading_graph import TradingGraph
from preferences import SUPPORTED_TICKERS, CONFIG

st.set_page_config(page_title="AgenticRAG Trading", page_icon="📈", layout="wide")

# ──────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Configuration")

ticker = st.sidebar.selectbox("📊 Ticker", SUPPORTED_TICKERS)
date = st.sidebar.date_input("📅 Analysis Date", datetime.now())
date_str = date.strftime("%Y-%m-%d")

st.sidebar.markdown("---")

# Portfolio input
st.sidebar.subheader("💼 Portfolio (Optional)")
st.sidebar.caption(
    "Add current holdings so the Risk Manager can give portfolio-aware advice."
)
portfolio = []
use_portfolio = st.sidebar.checkbox("Include portfolio holdings")
if use_portfolio:
    st.sidebar.markdown("**Format: one holding per line**")
    for t in SUPPORTED_TICKERS:
        col1, col2 = st.sidebar.columns(2)
        shares = col1.number_input(f"{t} shares", 0.0, key=f"shares_{t}", step=1.0)
        avg_price = col2.number_input(
            f"{t} avg $", 0.0, key=f"avg_{t}", step=0.01, format="%.2f"
        )
        if shares > 0:
            portfolio.append(
                {"ticker": t, "shares": shares, "avg_price": avg_price}
            )

st.sidebar.markdown("---")
with st.sidebar.expander("🔧 System Info"):
    st.write(f"**Provider:** {CONFIG['llm_provider']}")
    st.write(f"**Quick Model:** {CONFIG['quick_model']}")
    st.write(f"**Deep Model:** {CONFIG['deep_model']}")
    st.write(f"**Embeddings:** {CONFIG['embedding_provider']}")
    st.write(f"**Data Dir:** {CONFIG['data_dir']}")

# ──────────────────────────────────────────────────────────────────
# Main layout
# ──────────────────────────────────────────────────────────────────
st.title("📈 AgenticRAG Investment Decision System")
st.markdown("*Multi-Agent Multi-RAG Trading Analysis with Live Reasoning*")

# Agent pipeline definition (for status display)
AGENT_STEPS = [
    ("KB Pre-Query", "🧠", "Querying knowledge base for historical context…"),
    ("Fundamentals Analyst", "📊", "Analyzing company financials…"),
    ("Market Analyst", "📈", "Analyzing price action & technicals…"),
    ("News Analyst", "📰", "Scanning recent news & events…"),
    ("Social Analyst", "💬", "Analyzing social media sentiment…"),
    ("Bull Researcher", "🐂", "Building the bull case…"),
    ("Bear Researcher", "🐻", "Building the bear case…"),
    ("Research Manager", "🔬", "Synthesizing research debate…"),
    ("Risk Manager", "🛡️", "Assessing trade risk…"),
    ("Trader", "💰", "Making final decision…"),
    ("Explainability Report", "📋", "Generating explainability report…"),
    ("KB Post-Learn", "💾", "Storing decision in knowledge base…"),
]

# Map graph chunk keys → agent names
KEY_TO_AGENT = {
    "kb_pre_query": "KB Pre-Query",
    "fundamentals_analyst": "Fundamentals Analyst",
    "market_analyst": "Market Analyst",
    "news_analyst": "News Analyst",
    "social_analyst": "Social Analyst",
    "bull_researcher": "Bull Researcher",
    "bear_researcher": "Bear Researcher",
    "research_manager": "Research Manager",
    "risk_manager": "Risk Manager",
    "trader": "Trader",
    "explainability": "Explainability Report",
    "kb_post_learn": "KB Post-Learn",
}

# Map agent names → state keys that hold their output
AGENT_OUTPUT_KEY = {
    "KB Pre-Query": "historical_context",
    "Fundamentals Analyst": "fundamentals_report",
    "Market Analyst": "market_report",
    "News Analyst": "news_report",
    "Social Analyst": "social_report",
    "Bull Researcher": "bull_argument",
    "Bear Researcher": "bear_argument",
    "Research Manager": "research_summary",
    "Risk Manager": "risk_assessment",
    "Trader": "reasoning",
    "Explainability Report": "explainability_report",
}


def run_with_streaming(ticker, date_str, portfolio):
    """Run the pipeline and stream updates to the UI."""
    trading = TradingGraph()

    # Track statuses
    agent_status = {name: "⏳ pending" for name, _, _ in AGENT_STEPS}
    agent_outputs = {}
    final_state = {}

    # Layout: left = agent progress, right = latest report
    col_progress, col_report = st.columns([1, 2])

    with col_progress:
        st.subheader("🔄 Agent Pipeline")
        status_container = st.container()

    with col_report:
        st.subheader("📝 Latest Agent Output")
        report_container = st.empty()
        current_agent_label = st.empty()

    # Render initial status
    def render_status():
        with status_container:
            for name, icon, desc in AGENT_STEPS:
                s = agent_status[name]
                if "running" in s:
                    st.markdown(f"🔵 **{icon} {name}** — _running…_")
                elif "done" in s:
                    st.markdown(f"✅ {icon} {name}")
                else:
                    st.markdown(f"⏳ {icon} ~~{name}~~")

    # Stream execution
    for chunk in trading.stream(ticker, date_str, portfolio or None):
        # chunk is {node_name: {state_updates}}
        for node_key, updates in chunk.items():
            agent_name = KEY_TO_AGENT.get(node_key, node_key)

            # Mark this agent as done
            agent_status[agent_name] = "✅ done"

            # Mark the next agent as running
            agent_names = [n for n, _, _ in AGENT_STEPS]
            idx = agent_names.index(agent_name) if agent_name in agent_names else -1
            if idx + 1 < len(agent_names):
                agent_status[agent_names[idx + 1]] = "🔵 running"

            # Capture output
            output_key = AGENT_OUTPUT_KEY.get(agent_name)
            if output_key and output_key in updates:
                agent_outputs[agent_name] = updates[output_key]
                current_agent_label.markdown(f"**Last completed: {agent_name}**")
                report_container.text_area(
                    "",
                    value=str(updates[output_key]),
                    height=350,
                    disabled=True,
                    key=f"report_{agent_name}_{time.time()}",
                )

            # Merge into final state
            final_state.update(updates)

    # All done
    for name, _, _ in AGENT_STEPS:
        agent_status[name] = "✅ done"

    return final_state, agent_outputs, trading


# ──────────────────────────────────────────────────────────────────
# Run button
# ──────────────────────────────────────────────────────────────────
if st.button("🚀 Run Full Analysis", type="primary", use_container_width=True):
    st.markdown("---")

    try:
        final_state, agent_outputs, trading = run_with_streaming(
            ticker, date_str, portfolio
        )

        st.session_state["result"] = {
            "ticker": ticker,
            "date": date_str,
            "decision": final_state.get("final_decision", "HOLD"),
            "confidence": final_state.get("confidence", 0.5),
            "reasoning": final_state.get("reasoning", ""),
            "explainability_report": final_state.get("explainability_report", ""),
        }
        st.session_state["agent_outputs"] = agent_outputs
        st.session_state["kb_stats"] = trading.get_kb_stats()

        # Save result
        trading.save_result(st.session_state["result"])

    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.exception(e)

# ──────────────────────────────────────────────────────────────────
# Results display (persists after run)
# ──────────────────────────────────────────────────────────────────
if "result" in st.session_state:
    st.markdown("---")
    result = st.session_state["result"]
    decision = result["decision"]

    # Decision banner
    colors = {"BUY": "#28a745", "SELL": "#dc3545", "HOLD": "#ffc107"}
    text_colors = {"BUY": "white", "SELL": "white", "HOLD": "black"}
    bg = colors.get(decision, "#6c757d")
    fg = text_colors.get(decision, "white")

    st.markdown(
        f"""
        <div style="background-color:{bg}; padding:24px; border-radius:12px;
                    text-align:center; margin:16px 0;">
            <h1 style="color:{fg}; margin:0;">{decision}</h1>
            <p style="color:{fg}; margin:4px 0; font-size:1.2em;">
                Confidence: {result['confidence']:.1%}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Tabs for different views
    tab_reasoning, tab_agents, tab_explain, tab_kb = st.tabs(
        ["💭 Reasoning", "🤖 Agent Reports", "📋 Explainability", "🧠 Knowledge Base"]
    )

    with tab_reasoning:
        st.text_area(
            "Trader's Full Reasoning",
            result["reasoning"],
            height=400,
            disabled=True,
        )

    with tab_agents:
        agent_outputs = st.session_state.get("agent_outputs", {})
        for agent_name, output in agent_outputs.items():
            with st.expander(f"📄 {agent_name}", expanded=False):
                st.text_area(
                    agent_name,
                    value=str(output),
                    height=400,
                    disabled=True,
                    key=f"agent_report_{agent_name}",
                )

    with tab_explain:
        report = result.get("explainability_report", "")
        if report:
            st.text_area(
                "Full Explainability Report",
                report,
                height=500,
                disabled=True,
            )
            st.download_button(
                "📥 Download Report",
                data=report,
                file_name=f"explainability_{ticker}_{date_str}.txt",
                mime="text/plain",
            )
        else:
            st.info("No explainability report generated.")

    with tab_kb:
        stats = st.session_state.get("kb_stats", {})
        c1, c2, c3 = st.columns(3)
        c1.metric("📚 Market Insights", stats.get("market_insights", 0))
        c2.metric("📜 Trade History", stats.get("trade_history", 0))
        c3.metric("🎓 Lessons Learned", stats.get("lessons_learned", 0))
        st.caption(
            "Each analysis adds to the knowledge base. "
            "Future analyses will use these insights for better decisions."
        )

# ──────────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "*AgenticRAG — The Knowledge Base Agent actively learns from each decision. "
    "Run multiple analyses to build institutional memory.*"
)

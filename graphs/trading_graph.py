"""
Trading Graph - LangGraph workflow with FULL RAG integration.

Flow:
  KB Pre-Query → [4 Analysts in parallel] → Bull/Bear Researchers →
  Research Manager → Risk Manager → Trader → Explainability → KB Post-Learn

The KB Agent is used BEFORE (to provide historical context + lessons) and
AFTER (to store the decision, insights, and explainability report).
"""
import os
import sys
import json
import logging
from typing import Dict, Any, List, Callable
from datetime import datetime
from langgraph.graph import StateGraph, END

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.state import AgentState, create_state
from agents.kb_agent import KnowledgeBaseAgent
from agents.analysts import (
    create_fundamentals_analyst,
    create_market_analyst,
    create_news_analyst,
    create_social_analyst,
)
from agents.researchers import (
    create_bull_researcher,
    create_bear_researcher,
    create_research_manager,
)
from agents.risk_manager import create_risk_manager
from agents.trader import create_trader
from multi_rag.rag_manager import RAGManager
from multi_rag.explainability import Explainability
from dataflows.data_loader import DataLoader
from utils.llm_factory import get_quick_llm, get_deep_llm
from utils.portfolio_utils import build_portfolio_summary
from preferences import CONFIG, PRESET_PORTFOLIOS, DEFAULT_PORTFOLIO_KEY

logger = logging.getLogger(__name__)


def _log_step(name: str) -> Callable:
    """Wrapper that adds a log entry to agent_log whenever a node runs."""

    def decorator(fn):
        def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            log_entry = {
                "agent": name,
                "status": "running",
                "time": datetime.now().isoformat(),
            }
            existing_log = list(state.get("agent_log") or [])
            existing_log.append(log_entry)
            result = fn(state)
            # Mark completed
            log_entry["status"] = "done"
            result["agent_log"] = existing_log
            return result

        return wrapper

    return decorator


class TradingGraph:
    """
    Orchestrates the full multi-agent pipeline.

    Usage:
        tg = TradingGraph()
        result = tg.run("AAPL", "2024-01-15")
        # result includes decision, confidence, reasoning, explainability_report
    """

    def __init__(self, config: Dict = None):
        cfg = config or CONFIG
        self.quick_llm = get_quick_llm()
        # Use deep model for research manager (the "thinker")
        try:
            self.deep_llm = get_deep_llm()
        except Exception:
            self.deep_llm = self.quick_llm

        self.rag_manager = RAGManager()
        self.kb_agent = KnowledgeBaseAgent(self.rag_manager, self.quick_llm)
        self.explainability = Explainability(self.rag_manager, self.quick_llm)
        self.data_loader = DataLoader()
        self.graph = self._build_graph()

    # ------------------------------------------------------------------
    def _build_graph(self) -> StateGraph:
        # Create agent nodes
        fundamentals = create_fundamentals_analyst(self.quick_llm, self.data_loader)
        market = create_market_analyst(self.quick_llm, self.data_loader)
        news = create_news_analyst(self.quick_llm, self.data_loader)
        social = create_social_analyst(self.quick_llm, self.data_loader)
        bull = create_bull_researcher(self.quick_llm)
        bear = create_bear_researcher(self.quick_llm)
        research_mgr = create_research_manager(self.deep_llm)
        risk = create_risk_manager(self.quick_llm)
        trader = create_trader(self.deep_llm)

        # ----- Node wrappers with logging -----

        @_log_step("KB Pre-Query")
        def kb_pre_query(state: AgentState) -> Dict:
            result = self.kb_agent.pre_query(state["ticker"], state["date"])
            return {
                "historical_context": result["context"],
                "lessons": result["lessons"],
            }

        @_log_step("Fundamentals Analyst")
        def run_fundamentals(state):
            return fundamentals(state)

        @_log_step("Market Analyst")
        def run_market(state):
            return market(state)

        @_log_step("News Analyst")
        def run_news(state):
            return news(state)

        @_log_step("Social Analyst")
        def run_social(state):
            return social(state)

        @_log_step("Bull Researcher")
        def run_bull(state):
            return bull(state)

        @_log_step("Bear Researcher")
        def run_bear(state):
            return bear(state)

        @_log_step("Research Manager")
        def run_research_mgr(state):
            return research_mgr(state)

        @_log_step("Risk Manager")
        def run_risk(state):
            return risk(state)

        @_log_step("Trader")
        def run_trader(state):
            return trader(state)

        @_log_step("Explainability Report")
        def generate_explainability(state: AgentState) -> Dict:
            """Generate explainability report and store in RAG."""
            agent_outputs = {
                "fundamentals_report": state.get("fundamentals_report", ""),
                "market_report": state.get("market_report", ""),
                "news_report": state.get("news_report", ""),
                "social_report": state.get("social_report", ""),
                "bull_argument": state.get("bull_argument", ""),
                "bear_argument": state.get("bear_argument", ""),
                "research_summary": state.get("research_summary", ""),
                "risk_assessment": state.get("risk_assessment", ""),
            }
            report = self.explainability.generate_report(
                ticker=state["ticker"],
                date=state["date"],
                decision=state.get("final_decision", "HOLD"),
                confidence=state.get("confidence", 0.5),
                agent_outputs=agent_outputs,
                reasoning=state.get("reasoning", ""),
                portfolio=state.get("portfolio"),
            )
            # Store report in RAG
            self.explainability.store_report(state["ticker"], state["date"], report)
            return {"explainability_report": report}

        @_log_step("KB Post-Learn")
        def kb_post_learn(state: AgentState) -> Dict:
            """Store the decision + agent insights in the knowledge base."""
            self.kb_agent.post_learn(
                ticker=state["ticker"],
                date=state["date"],
                decision=state.get("final_decision", "HOLD"),
                reasoning=state.get("reasoning", ""),
                agent_outputs={
                    "fundamentals": state.get("fundamentals_report", ""),
                    "market": state.get("market_report", ""),
                    "news": state.get("news_report", ""),
                    "social": state.get("social_report", ""),
                },
                confidence=state.get("confidence", 0.5),
            )
            return {}

        # ----- Build the graph -----
        workflow = StateGraph(AgentState)

        workflow.add_node("kb_pre_query", kb_pre_query)
        workflow.add_node("fundamentals_analyst", run_fundamentals)
        workflow.add_node("market_analyst", run_market)
        workflow.add_node("news_analyst", run_news)
        workflow.add_node("social_analyst", run_social)
        workflow.add_node("bull_researcher", run_bull)
        workflow.add_node("bear_researcher", run_bear)
        workflow.add_node("research_manager", run_research_mgr)
        workflow.add_node("risk_manager", run_risk)
        workflow.add_node("trader", run_trader)
        workflow.add_node("explainability", generate_explainability)
        workflow.add_node("kb_post_learn", kb_post_learn)

        # ----- Edges -----
        workflow.set_entry_point("kb_pre_query")

        # Analysts run sequentially (LangGraph free tier has no fan-out)
        workflow.add_edge("kb_pre_query", "fundamentals_analyst")
        workflow.add_edge("fundamentals_analyst", "market_analyst")
        workflow.add_edge("market_analyst", "news_analyst")
        workflow.add_edge("news_analyst", "social_analyst")

        # Research debate
        workflow.add_edge("social_analyst", "bull_researcher")
        workflow.add_edge("bull_researcher", "bear_researcher")
        workflow.add_edge("bear_researcher", "research_manager")

        # Risk + Trade
        workflow.add_edge("research_manager", "risk_manager")
        workflow.add_edge("risk_manager", "trader")

        # Post-decision: explainability → store in KB
        workflow.add_edge("trader", "explainability")
        workflow.add_edge("explainability", "kb_post_learn")
        workflow.add_edge("kb_post_learn", END)

        return workflow.compile()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, ticker: str, date: str, portfolio: list = None) -> Dict[str, Any]:
        """Run the full analysis pipeline."""
        # Default to preset portfolio if none provided
        if portfolio is None:
            portfolio = PRESET_PORTFOLIOS[DEFAULT_PORTFOLIO_KEY]["holdings"]
        portfolio_summary = build_portfolio_summary(portfolio, ticker)

        initial_state = create_state(ticker, date, portfolio)
        initial_state["portfolio_summary"] = portfolio_summary
        final_state = self.graph.invoke(initial_state)
        return {
            "ticker": ticker,
            "date": date,
            "decision": final_state.get("final_decision", "HOLD"),
            "confidence": final_state.get("confidence", 0.5),
            "reasoning": final_state.get("reasoning", ""),
            "explainability_report": final_state.get("explainability_report", ""),
            "agent_log": final_state.get("agent_log", []),
            "state": final_state,
        }

    def stream(self, ticker: str, date: str, portfolio: list = None):
        """Stream the pipeline step-by-step (for live UI updates)."""
        # Default to preset portfolio if none provided
        if portfolio is None:
            portfolio = PRESET_PORTFOLIOS[DEFAULT_PORTFOLIO_KEY]["holdings"]
        portfolio_summary = build_portfolio_summary(portfolio, ticker)

        initial_state = create_state(ticker, date, portfolio)
        initial_state["portfolio_summary"] = portfolio_summary
        for chunk in self.graph.stream(initial_state):
            yield chunk

    def get_kb_stats(self) -> Dict[str, int]:
        return self.kb_agent.get_stats()

    def learn_from_outcome(self, ticker, date, decision, reasoning, actual_return):
        """Feed back actual returns to teach the RAG."""
        return self.explainability.learn_from_outcome(
            ticker, date, decision, reasoning, actual_return
        )

    def save_result(self, result: Dict, directory: str = None):
        """Save result to results/ directory."""
        directory = directory or CONFIG.get("results_dir", "./results")
        os.makedirs(directory, exist_ok=True)
        filename = f"{result['ticker']}_{result['date']}.json"
        path = os.path.join(directory, filename)
        # Save everything except the full state (too verbose)
        save_data = {k: v for k, v in result.items() if k != "state"}
        with open(path, "w") as f:
            json.dump(save_data, f, indent=2, default=str)
        return path

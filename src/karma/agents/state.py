"""
Agent State - Shared state for all agents.
Includes portfolio holdings for risk-aware analysis.
"""
from typing import TypedDict, List, Dict, Any, Optional


class PortfolioHolding(TypedDict):
    ticker: str
    shares: float
    avg_price: float


class AgentState(TypedDict):
    # Input
    ticker: str
    date: str
    # RAG context from KB Agent
    historical_context: str
    lessons: List[str]
    # Portfolio (optional)
    portfolio: List[PortfolioHolding]
    portfolio_summary: str
    # Analyst reports
    fundamentals_report: str
    market_report: str
    news_report: str
    social_report: str
    # Research debate
    bull_argument: str
    bear_argument: str
    research_summary: str
    # Risk + decision
    risk_assessment: str
    final_decision: str
    confidence: float
    reasoning: str
    # Explainability report (generated at end)
    explainability_report: str
    # Step tracking for live UI
    agent_log: List[Dict[str, Any]]


def create_state(
    ticker: str, date: str, portfolio: list = None, portfolio_summary: str = ""
) -> AgentState:
    return AgentState(
        ticker=ticker,
        date=date,
        historical_context="",
        lessons=[],
        portfolio=portfolio or [],
        portfolio_summary=portfolio_summary,
        fundamentals_report="",
        market_report="",
        news_report="",
        social_report="",
        bull_argument="",
        bear_argument="",
        research_summary="",
        risk_assessment="",
        final_decision="",
        confidence=0.0,
        reasoning="",
        explainability_report="",
        agent_log=[],
    )

"""
KARMA Risk Manager — Portfolio-aware risk assessment for intraday trading.
"""
from typing import Dict, Any
from .prompts import RISK_PROMPT
from karma.utils.core import extract_llm_text


def create_risk_manager(llm):
    """Create risk manager agent (portfolio-aware)."""

    def risk_node(state: Dict[str, Any]) -> Dict[str, Any]:
        proposal = state.get("research_summary", "No proposal available")
        portfolio_summary = state.get("portfolio_summary", "No portfolio context.")

        prompt = RISK_PROMPT.format(
            proposal=proposal,
            portfolio_summary=portfolio_summary,
        )
        response = llm.invoke(prompt)

        return {"risk_assessment": extract_llm_text(response)}

    return risk_node

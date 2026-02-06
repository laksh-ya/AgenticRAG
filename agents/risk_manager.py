"""
Risk Manager - Portfolio-aware risk assessment.
"""
from typing import Dict, Any
from .prompts import RISK_PROMPT


def create_risk_manager(llm):
    """Create risk manager agent (portfolio-aware)."""

    def risk_node(state: Dict[str, Any]) -> Dict[str, Any]:
        proposal = state.get("research_summary", "No proposal available")

        # Add portfolio context if available
        portfolio = state.get("portfolio", [])
        portfolio_info = ""
        if portfolio:
            portfolio_info = "\n\nCurrent Portfolio Holdings:\n"
            for h in portfolio:
                portfolio_info += (
                    f"  - {h['ticker']}: {h['shares']} shares @ ${h['avg_price']:.2f}\n"
                )
            portfolio_info += (
                "\nConsider existing exposure, concentration risk, "
                "and how this trade affects the overall portfolio."
            )

        prompt = RISK_PROMPT.format(proposal=proposal) + portfolio_info
        response = llm.invoke(prompt)
        assessment = response.content if hasattr(response, "content") else str(response)

        return {"risk_assessment": assessment}

    return risk_node

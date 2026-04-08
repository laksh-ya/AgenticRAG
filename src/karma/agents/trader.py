"""
KARMA Trader — Makes the final BUY/HOLD/SELL intraday decision.
"""
import re
from typing import Dict, Any
from .prompts import TRADER_PROMPT
from karma.utils.core import extract_llm_text


def create_trader(llm):
    """Create trader agent."""
    
    def trader_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Make final trading decision."""
        lessons = "\n".join(state.get("lessons", ["No past lessons."]))
        
        prompt = TRADER_PROMPT.format(
            research=state.get("research_summary", "No research"),
            risk=state.get("risk_assessment", "No risk assessment"),
            lessons=lessons,
            portfolio_summary=state.get("portfolio_summary", "No portfolio context."),
        )
        
        response = llm.invoke(prompt)
        content = extract_llm_text(response)
        
        # Extract decision
        decision = extract_decision(content)
        confidence = extract_confidence(content)
        
        return {
            "final_decision": decision,
            "confidence": confidence,
            "reasoning": content
        }
    
    return trader_node


def extract_decision(content: str) -> str:
    """Extract BUY/HOLD/SELL from response."""
    content_upper = content.upper()
    
    # Look for explicit format
    patterns = [
        r"FINAL DECISION:\s*\*\*(\w+)\*\*",
        r"FINAL DECISION:\s*(\w+)",
        r"DECISION:\s*\*\*(\w+)\*\*",
        r"DECISION:\s*(\w+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content_upper)
        if match:
            decision = match.group(1)
            if decision in ["BUY", "SELL", "HOLD"]:
                return decision
    
    # Fallback: look for keywords
    if "BUY" in content_upper and "SELL" not in content_upper:
        return "BUY"
    elif "SELL" in content_upper and "BUY" not in content_upper:
        return "SELL"
    return "HOLD"


def extract_confidence(content: str) -> float:
    """Extract confidence score from response."""
    # Look for patterns like "confidence: 0.8" or "0.75"
    patterns = [
        r"confidence[:\s]+([0-9]+\.?[0-9]*)",
        r"([0-9]+\.?[0-9]*)\s*confidence",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content.lower())
        if match:
            try:
                conf = float(match.group(1))
                if 0 <= conf <= 1:
                    return conf
                elif 1 < conf <= 100:
                    return conf / 100
            except ValueError:
                pass
    
    return 0.5  # Default

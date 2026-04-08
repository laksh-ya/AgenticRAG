"""
KARMA Researchers — Bull/Bear debate and Research Manager.
Uses shared utilities for LLM response handling.
"""
from typing import Dict, Any
from .prompts import BULL_PROMPT, BEAR_PROMPT, RESEARCH_MANAGER_PROMPT
from karma.utils.core import extract_llm_text


def create_bull_researcher(llm):
    """Create bull researcher agent."""
    
    def bull_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Make the bullish case."""
        reports = f"""
Fundamentals: {state.get('fundamentals_report', 'N/A')}
Market: {state.get('market_report', 'N/A')}
News: {state.get('news_report', 'N/A')}
Social: {state.get('social_report', 'N/A')}
"""
        lessons = "\n".join(state.get("lessons", ["No past lessons."]))
        portfolio_summary = state.get("portfolio_summary", "No portfolio context.")
        
        prompt = BULL_PROMPT.format(reports=reports, lessons=lessons, portfolio_summary=portfolio_summary)
        response = llm.invoke(prompt)
        
        return {"bull_argument": extract_llm_text(response)}
    
    return bull_node


def create_bear_researcher(llm):
    """Create bear researcher agent."""
    
    def bear_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Make the bearish case."""
        reports = f"""
Fundamentals: {state.get('fundamentals_report', 'N/A')}
Market: {state.get('market_report', 'N/A')}
News: {state.get('news_report', 'N/A')}
Social: {state.get('social_report', 'N/A')}
"""
        lessons = "\n".join(state.get("lessons", ["No past lessons."]))
        portfolio_summary = state.get("portfolio_summary", "No portfolio context.")
        
        prompt = BEAR_PROMPT.format(reports=reports, lessons=lessons, portfolio_summary=portfolio_summary)
        response = llm.invoke(prompt)
        
        return {"bear_argument": extract_llm_text(response)}
    
    return bear_node


def create_research_manager(llm):
    """Create research manager agent."""
    
    def manager_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize bull/bear debate."""
        prompt = RESEARCH_MANAGER_PROMPT.format(
            bull=state.get("bull_argument", "No bull argument"),
            bear=state.get("bear_argument", "No bear argument"),
            portfolio_summary=state.get("portfolio_summary", "No portfolio context."),
        )
        
        response = llm.invoke(prompt)
        
        return {"research_summary": extract_llm_text(response)}
    
    return manager_node

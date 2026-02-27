"""
Researchers - Bull and Bear researchers + Research Manager
"""
from typing import Dict, Any
from .prompts import BULL_PROMPT, BEAR_PROMPT, RESEARCH_MANAGER_PROMPT


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
        argument = response.content if hasattr(response, 'content') else str(response)
        
        return {"bull_argument": argument}
    
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
        argument = response.content if hasattr(response, 'content') else str(response)
        
        return {"bear_argument": argument}
    
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
        summary = response.content if hasattr(response, 'content') else str(response)
        
        return {"research_summary": summary}
    
    return manager_node

"""
Analysts - All 4 analyst agents in one file
Simple, easy to understand
"""
from typing import Dict, Any
from .prompts import FUNDAMENTALS_PROMPT, MARKET_PROMPT, NEWS_PROMPT, SOCIAL_PROMPT


def create_analyst(llm, analyst_type: str, data_loader):
    """
    Create an analyst agent.
    
    Args:
        llm: Language model
        analyst_type: "fundamentals", "market", "news", or "social"
        data_loader: DataLoader instance
    
    Returns:
        Analyst function for LangGraph
    """
    prompts = {
        "fundamentals": FUNDAMENTALS_PROMPT,
        "market": MARKET_PROMPT,
        "news": NEWS_PROMPT,
        "social": SOCIAL_PROMPT,
    }
    
    prompt_template = prompts.get(analyst_type, FUNDAMENTALS_PROMPT)
    report_key = f"{analyst_type}_report"
    
    def analyst_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the analyst."""
        ticker = state["ticker"]
        date = state["date"]
        context = state.get("historical_context", "No historical context.")
        
        # Load data for this analyst
        data = data_loader.load(ticker, date, analyst_type)
        
        # Format prompt
        prompt = prompt_template.format(
            ticker=ticker,
            date=date,
            context=context,
            data=data
        )
        
        # Get response
        response = llm.invoke(prompt)
        report = response.content if hasattr(response, 'content') else str(response)
        
        return {report_key: report}
    
    return analyst_node


def create_fundamentals_analyst(llm, data_loader):
    """Create fundamentals analyst."""
    return create_analyst(llm, "fundamentals", data_loader)


def create_market_analyst(llm, data_loader):
    """Create market analyst."""
    return create_analyst(llm, "market", data_loader)


def create_news_analyst(llm, data_loader):
    """Create news analyst."""
    return create_analyst(llm, "news", data_loader)


def create_social_analyst(llm, data_loader):
    """Create social media analyst."""
    return create_analyst(llm, "social", data_loader)

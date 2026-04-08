"""
KARMA Core Utilities — Shared helpers used across the codebase.

This module consolidates common patterns to avoid duplication:
- LLM response extraction
- Decision evaluation logic
- Price fetching with caching
- Date/time helpers
"""
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)

# =============================================================================
# LLM RESPONSE HANDLING
# =============================================================================

def extract_llm_text(response: Any) -> str:
    """
    Extract text content from any LLM response object.
    Works with LangChain, OpenAI, and custom response types.
    """
    if hasattr(response, 'content'):
        return response.content
    return str(response)


# =============================================================================
# DECISION EVALUATION
# =============================================================================

def evaluate_decision(decision: str, actual_return: float) -> bool:
    """
    Evaluate if a trading decision was correct given the actual return.
    
    Rules:
    - BUY is correct if return > 0
    - SELL is correct if return < 0  
    - HOLD is correct if |return| < 5%
    
    Args:
        decision: "BUY", "SELL", or "HOLD"
        actual_return: Decimal return (e.g., 0.05 for +5%)
    
    Returns:
        True if decision was correct
    """
    d = decision.upper()
    if d == "BUY":
        return actual_return > 0
    elif d == "SELL":
        return actual_return < 0
    else:  # HOLD
        return abs(actual_return) < 0.05


def generate_lesson(decision: str, actual_return: float, 
                    was_correct: bool, reasoning: str = "") -> str:
    """
    Generate a lesson string from a trading outcome.
    Used by KB agent and explainability module.
    """
    if was_correct:
        return (
            f"SUCCESSFUL {decision} ({actual_return:+.2%} return). "
            f"Analysis correctly identified direction. "
            f"Trust similar signals in future. "
            f"Reasoning: {reasoning[:200]}"
        )
    else:
        return (
            f"FAILED {decision} ({actual_return:+.2%} return). "
            f"Analysis missed key factors — be more cautious "
            f"with similar setups. "
            f"Original reasoning: {reasoning[:200]}"
        )


# =============================================================================
# PRICE CACHING
# =============================================================================

# Module-level price cache: {ticker_date: price}
_price_cache: Dict[str, float] = {}


def fetch_price(ticker: str, fallback: float = 0.0) -> Tuple[float, bool]:
    """
    Fetch current price with caching. Uses yfinance.
    
    Args:
        ticker: Stock ticker symbol
        fallback: Price to use if fetch fails
    
    Returns:
        (price, is_stale) where is_stale=True means fetch failed
    """
    cache_key = f"{ticker}_{datetime.now().strftime('%Y-%m-%d')}"
    
    if cache_key in _price_cache:
        return _price_cache[cache_key], False
    
    try:
        import yfinance as yf
        data = yf.Ticker(ticker).history(period="5d")
        if data.empty:
            logger.warning("No price data for %s, using fallback", ticker)
            return fallback, True
        price = float(data["Close"].iloc[-1])
        _price_cache[cache_key] = price
        return price, False
    except Exception as e:
        logger.warning("Price fetch failed for %s: %s", ticker, e)
        return fallback, True


def clear_price_cache():
    """Clear the price cache (useful for testing)."""
    _price_cache.clear()


# =============================================================================
# DATE HELPERS
# =============================================================================

def get_business_days(start: date, n: int) -> List[date]:
    """
    Get the next n business days starting from start date.
    
    Args:
        start: Starting date
        n: Number of business days to return
    
    Returns:
        List of business day dates
    """
    days = []
    current = start
    while len(days) < n:
        if current.weekday() < 5:  # Monday=0, Friday=4
            days.append(current)
        current += timedelta(days=1)
    return days


def next_business_day(d: date) -> date:
    """Get the next business day after the given date."""
    next_day = d + timedelta(days=1)
    while next_day.weekday() >= 5:  # Skip weekends
        next_day += timedelta(days=1)
    return next_day


def format_timestamp(iso_str: str, fmt: str = "%I:%M %p") -> str:
    """
    Format an ISO timestamp string to a human-readable format.
    
    Args:
        iso_str: ISO format datetime string
        fmt: strftime format string
    
    Returns:
        Formatted string, or empty string on parse failure
    """
    try:
        return datetime.fromisoformat(iso_str).strftime(fmt)
    except (ValueError, TypeError):
        return ""


# =============================================================================
# TEXT HELPERS  
# =============================================================================

def truncate(text: str, max_len: int = 300, suffix: str = "...") -> str:
    """Truncate text to max_len characters with suffix."""
    if len(text) <= max_len:
        return text
    return text[:max_len - len(suffix)] + suffix


def is_investment_relevant(text: str) -> bool:
    """
    Check if text is relevant for investment analysis.
    Filters out spam, ads, and off-topic content.
    """
    if not text or len(text.strip()) < 20:
        return False
    
    lower = text.lower()
    
    # Exclude patterns
    exclude = [
        "free stock", "sign up", "click here", "limited time",
        "giveaway", "promo code", "referral", "subscribe",
        "not financial advice", "i am not a financial advisor"
    ]
    if any(e in lower for e in exclude):
        return False
    
    # Must have some investment-related content
    include = [
        "stock", "share", "price", "buy", "sell", "hold",
        "market", "earnings", "revenue", "profit", "growth",
        "analyst", "target", "rating", "bullish", "bearish"
    ]
    return any(i in lower for i in include)

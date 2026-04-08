"""
KARMA Utilities Package

Consolidated utilities for the KARMA framework:
- core: LLM helpers, decision evaluation, price caching, date helpers
- llm_factory: LLM instance creation from config
- portfolio_utils: Portfolio summary generation
"""
from .core import (
    extract_llm_text,
    evaluate_decision,
    generate_lesson,
    fetch_price,
    clear_price_cache,
    get_business_days,
    next_business_day,
    format_timestamp,
    truncate,
    is_investment_relevant,
)
from .llm_factory import create_llm, get_deep_llm, get_quick_llm
from .portfolio_utils import build_portfolio_summary

__all__ = [
    # Core utilities
    "extract_llm_text",
    "evaluate_decision", 
    "generate_lesson",
    "fetch_price",
    "clear_price_cache",
    "get_business_days",
    "next_business_day",
    "format_timestamp",
    "truncate",
    "is_investment_relevant",
    # LLM factory
    "create_llm",
    "get_deep_llm", 
    "get_quick_llm",
    # Portfolio
    "build_portfolio_summary",
]

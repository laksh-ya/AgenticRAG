"""
AgenticRAG Preferences - Central Configuration Hub
Switch LLMs, embeddings, and data sources here. NO HARDCODING.
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# SUPPORTED STOCKS
# =============================================================================
SUPPORTED_TICKERS = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN"]

# =============================================================================
# LLM PROVIDERS - Easy to switch
# =============================================================================
LLM_PROVIDERS = {
    "openai": {
        "deep": ["gpt-4o", "gpt-4-turbo", "o1-preview"],
        "quick": ["gpt-4o-mini", "gpt-3.5-turbo"],
        "default_deep": "gpt-4o-mini",
        "default_quick": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
        "base_url": None,
    },
    "gemini": {
        "deep": ["gemini-2.5-pro", "gemini-2.5-flash"],
        "quick": ["gemini-2.5-flash-lite", "gemini-2.0-flash"],
        "default_deep": "gemini-2.5-flash",
        "default_quick": "gemini-2.5-flash-lite",
        "api_key_env": "GOOGLE_API_KEY",
        "base_url": None,
    },
    "ollama": {
        "deep": ["llama3.1:70b", "mixtral:8x7b"],
        "quick": ["llama3.1:8b", "mistral:7b"],
        "default_deep": "llama3.1:8b",
        "default_quick": "mistral:7b",
        "api_key_env": None,
        "base_url": "http://localhost:11434/v1",
    },
}

# =============================================================================
# EMBEDDING PROVIDERS
# =============================================================================
EMBEDDING_PROVIDERS = {
    "openai": {
        "model": "text-embedding-3-small",
        "api_key_env": "OPENAI_API_KEY",
    },
    "gemini": {
        "model": "models/embedding-001",
        "api_key_env": "GOOGLE_API_KEY",
    },
    "ollama": {
        "model": "nomic-embed-text",
        "api_key_env": None,
    },
}

# =============================================================================
# DATA FALLBACK CHAINS - Tried in order after JSON cache miss
# Each list names sources from dataflows/sources.py SOURCE_REGISTRY
# =============================================================================
FALLBACK_CHAINS = {
    "fundamentals": ["yfinance", "alpha_vantage"],
    "market":       ["yfinance", "yfinance_report"],
    "technical":    ["yfinance"],
    "news":         ["google_rss", "alpha_vantage"],
    "social":       ["reddit", "stocktwits"],
}

# =============================================================================
# CACHE TTLs (seconds) - How long cached JSON stays fresh before re-fetching
# =============================================================================
CACHE_TTL = {
    "fundamentals": 7 * 24 * 3600,   # 7 days  (quarterly data, rarely changes)
    "market":       24 * 3600,        # 1 day
    "technical":    24 * 3600,        # 1 day
    "news":         6 * 3600,         # 6 hours
    "social":       6 * 3600,         # 6 hours
}

# =============================================================================
# ACTIVE CONFIGURATION - What's currently being used
# =============================================================================
CONFIG = {
    # LLM Settings
    "llm_provider": "openai",
    "deep_model": "gpt-4o",
    "quick_model": "gpt-4o-mini",
    
    # Embedding Settings
    "embedding_provider": "openai",
    
    # Data pipeline
    "fallback_chains": FALLBACK_CHAINS,
    "cache_ttl": CACHE_TTL,
    "alpha_vantage_api_key": os.getenv("ALPHA_VANTAGE_API_KEY", ""),

    # Agents
    "selected_analysts": ["fundamentals", "market", "news", "social_media"],
    "max_debate_rounds": 1,
    
    # Paths
    "data_dir": "./data",
    "knowledge_base_dir": "./knowledge_base",
    "results_dir": "./results",
    "logs_dir": "./logs",
}


# =============================================================================
# HELPER FUNCTIONS - No hardcoding, easy switching
# =============================================================================

def get_config() -> Dict[str, Any]:
    """Get a copy of current config."""
    return CONFIG.copy()


def set_config(key: str, value: Any):
    """Update config at runtime."""
    CONFIG[key] = value


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a provider from environment."""
    if provider in LLM_PROVIDERS:
        env_var = LLM_PROVIDERS[provider].get("api_key_env")
        return os.getenv(env_var) if env_var else None
    if provider in EMBEDDING_PROVIDERS:
        env_var = EMBEDDING_PROVIDERS[provider].get("api_key_env")
        return os.getenv(env_var) if env_var else None
    return None


def get_llm_info(provider: str = None) -> Dict[str, Any]:
    """Get LLM provider info."""
    provider = provider or CONFIG["llm_provider"]
    return LLM_PROVIDERS.get(provider, {})


def get_embedding_info(provider: str = None) -> Dict[str, Any]:
    """Get embedding provider info."""
    provider = provider or CONFIG["embedding_provider"]
    return EMBEDDING_PROVIDERS.get(provider, {})


def validate_config() -> list:
    """Check if config is valid, return list of issues."""
    issues = []
    
    # Check LLM API key
    provider = CONFIG["llm_provider"]
    if provider != "ollama" and not get_api_key(provider):
        env_var = LLM_PROVIDERS[provider]["api_key_env"]
        issues.append(f"Missing {env_var}")
    
    return issues

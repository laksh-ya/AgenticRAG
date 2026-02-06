"""
LLM Factory - Create LLM instances from config
No hardcoding - reads from preferences.py
"""
from typing import Optional
from langchain_openai import ChatOpenAI

from preferences import CONFIG, LLM_PROVIDERS, get_api_key


def create_llm(
    model: str = None,
    provider: str = None,
    temperature: float = 0.7
) -> ChatOpenAI:
    """
    Create an LLM instance from config.
    
    Args:
        model: Model name. Uses config default if None.
        provider: Provider name. Uses config default if None.
        temperature: Temperature setting.
    
    Returns:
        ChatOpenAI instance (works with OpenAI-compatible APIs)
    """
    provider = provider or CONFIG["llm_provider"]
    provider_info = LLM_PROVIDERS.get(provider, {})
    
    # Get model
    if model is None:
        model = CONFIG.get("quick_model") or provider_info.get("default_quick")
    
    # Get API key and base URL
    api_key = get_api_key(provider)
    base_url = provider_info.get("base_url")
    
    # For Gemini, we need langchain-google-genai
    if provider == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                google_api_key=api_key,
            )
        except ImportError:
            raise ImportError("Install langchain-google-genai for Gemini support")
    
    # Check API key for non-Ollama providers
    if provider != "ollama" and not api_key:
        raise ValueError(
            f"Missing API key for {provider}. "
            f"Set {LLM_PROVIDERS[provider]['api_key_env']} in your .env file."
        )
    
    # OpenAI and Ollama use OpenAI-compatible API
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key or "not-needed",  # Ollama doesn't need key
        base_url=base_url,
    )


def get_deep_llm(temperature: float = 0.7):
    """Get the deep thinking LLM from config."""
    return create_llm(
        model=CONFIG.get("deep_model"),
        temperature=temperature
    )


def get_quick_llm(temperature: float = 0.7):
    """Get the quick thinking LLM from config."""
    return create_llm(
        model=CONFIG.get("quick_model"),
        temperature=temperature
    )

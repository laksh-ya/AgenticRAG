"""
Embeddings - Create embeddings from text
Supports OpenAI, Gemini, Ollama (no hardcoding)
"""
import os
from typing import List
from openai import OpenAI

from karma.config import CONFIG, EMBEDDING_PROVIDERS, get_api_key


class Embeddings:
    """Simple embeddings class - works with OpenAI, Gemini, Ollama."""
    
    def __init__(self, provider: str = None):
        """
        Initialize embeddings.
        
        Args:
            provider: "openai", "gemini", or "ollama". Uses config default if None.
        """
        self.provider = provider or CONFIG["embedding_provider"]
        self.info = EMBEDDING_PROVIDERS.get(self.provider, {})
        self.model = self.info.get("model", "text-embedding-3-small")
        self._setup()
    
    def _setup(self):
        """Setup the embedding provider."""
        if self.provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=get_api_key("gemini"))
                self.genai = genai
            except ImportError:
                raise ImportError("Install google-generativeai for Gemini embeddings")
        else:
            # OpenAI or Ollama (both use OpenAI-compatible API)
            base_url = None
            if self.provider == "ollama":
                base_url = "http://localhost:11434/v1"
            
            api_key = get_api_key("openai")
            if not api_key and self.provider != "ollama":
                raise ValueError(
                    "Missing OPENAI_API_KEY for embeddings. "
                    "Set it in your .env file."
                )
            self.client = OpenAI(
                api_key=api_key or "not-needed",
                base_url=base_url
            )
    
    def embed(self, text: str) -> List[float]:
        """Embed a single text."""
        return self.embed_batch([text])[0]
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        if self.provider == "gemini":
            embeddings = []
            for text in texts:
                result = self.genai.embed_content(
                    model=self.model,
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
            return embeddings
        else:
            # OpenAI or Ollama
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]


def get_embeddings(provider: str = None) -> Embeddings:
    """Factory function to get embeddings."""
    return Embeddings(provider)

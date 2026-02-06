"""
RAG Manager - Manages multiple knowledge stores
Simple, easy to understand
"""
import os
from typing import Dict, List, Any, Optional

from .knowledge_store import KnowledgeStore
from .embeddings import Embeddings, get_embeddings

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preferences import CONFIG


class RAGManager:
    """
    Manages 3 RAG stores:
    - market_insights: Historical market patterns
    - trade_history: Past decisions and outcomes
    - lessons_learned: What went right/wrong
    """
    
    STORES = ["market_insights", "trade_history", "lessons_learned"]
    
    def __init__(self, persist_dir: str = None):
        """
        Initialize RAG Manager.
        
        Args:
            persist_dir: Directory to persist data. Uses config default if None.
        """
        self.persist_dir = persist_dir or CONFIG.get("knowledge_base_dir", "./knowledge_base")
        self.embeddings = get_embeddings()
        
        # Create stores
        self.stores: Dict[str, KnowledgeStore] = {}
        for name in self.STORES:
            self.stores[name] = KnowledgeStore(
                name=name,
                persist_dir=self.persist_dir,
                embeddings=self.embeddings
            )
    
    def add(self, store_name: str, texts: List[str], metadatas: List[Dict] = None) -> List[str]:
        """Add documents to a store."""
        if store_name not in self.stores:
            raise ValueError(f"Unknown store: {store_name}")
        return self.stores[store_name].add(texts, metadatas)
    
    def query(self, store_name: str, query: str, n: int = 5) -> List[Dict]:
        """Query a specific store."""
        if store_name not in self.stores:
            raise ValueError(f"Unknown store: {store_name}")
        return self.stores[store_name].query(query, n)
    
    def query_all(self, query: str, n_per_store: int = 3) -> Dict[str, List[Dict]]:
        """Query all stores and return combined results."""
        results = {}
        for name, store in self.stores.items():
            store_results = store.query(query, n_per_store)
            if store_results:
                results[name] = store_results
        return results
    
    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================
    
    def store_decision(
        self,
        ticker: str,
        date: str,
        decision: str,
        reasoning: str,
        confidence: float = None
    ) -> str:
        """Store a trading decision in trade_history."""
        text = f"""
TICKER: {ticker}
DATE: {date}
DECISION: {decision}
CONFIDENCE: {confidence or 'N/A'}

REASONING:
{reasoning}
"""
        metadata = {
            "ticker": ticker,
            "date": date,
            "decision": decision,
            "type": "decision"
        }
        ids = self.add("trade_history", [text], [metadata])
        return ids[0] if ids else None
    
    def store_lesson(
        self,
        ticker: str,
        date: str,
        lesson: str,
        was_correct: bool,
        actual_return: float = None
    ) -> str:
        """Store a lesson learned."""
        outcome = "✅ CORRECT" if was_correct else "❌ WRONG"
        return_str = f"{actual_return:.2%}" if actual_return else "N/A"
        
        text = f"""
TICKER: {ticker}
DATE: {date}
OUTCOME: {outcome}
RETURN: {return_str}

LESSON:
{lesson}
"""
        metadata = {
            "ticker": ticker,
            "date": date,
            "was_correct": was_correct,
            "actual_return": actual_return,
            "type": "lesson"
        }
        ids = self.add("lessons_learned", [text], [metadata])
        return ids[0] if ids else None
    
    def store_insight(self, ticker: str, insight: str, metadata: Dict = None) -> str:
        """Store a market insight."""
        meta = {"ticker": ticker, "type": "insight", **(metadata or {})}
        ids = self.add("market_insights", [insight], [meta])
        return ids[0] if ids else None
    
    def get_context_for_ticker(self, ticker: str, n: int = 3) -> Dict[str, List[Dict]]:
        """Get all relevant context for a ticker."""
        return self.query_all(f"Analysis and history for {ticker}", n)
    
    def get_stats(self) -> Dict[str, int]:
        """Get document counts for all stores."""
        return {name: store.count() for name, store in self.stores.items()}
    
    def clear_all(self):
        """Clear all stores."""
        for store in self.stores.values():
            store.clear()

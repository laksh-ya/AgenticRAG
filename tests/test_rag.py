"""
Test RAG module
"""
import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))


class TestRAGManager:
    """Test Multi-RAG system."""
    
    def setup_method(self):
        from karma.rag.rag_manager import RAGManager
        self.rag = RAGManager()  # In-memory
    
    def test_add_and_query(self):
        """Test adding and querying."""
        # Add document
        ids = self.rag.add(
            "market_insights",
            ["AAPL shows strong momentum"],
            [{"ticker": "AAPL"}]
        )
        assert len(ids) == 1
        
        # Query
        results = self.rag.query("market_insights", "AAPL momentum")
        assert len(results) > 0
        assert "AAPL" in results[0]["text"]
    
    def test_query_all(self):
        """Test querying all stores."""
        # Add to different stores
        self.rag.add("market_insights", ["Market insight 1"])
        self.rag.add("trade_history", ["Trade decision 1"])
        self.rag.add("lessons_learned", ["Lesson 1"])
        
        # Query all
        results = self.rag.query_all("analysis")
        assert "market_insights" in results or "trade_history" in results
    
    def test_store_decision(self):
        """Test convenience method."""
        id = self.rag.store_decision(
            ticker="NVDA",
            date="2024-01-15",
            decision="BUY",
            reasoning="AI boom"
        )
        assert id is not None
    
    def test_store_lesson(self):
        """Test storing lessons."""
        id = self.rag.store_lesson(
            ticker="GOOGL",
            date="2024-01-15",
            lesson="Should have sold earlier",
            was_correct=False,
            actual_return=-0.03
        )
        assert id is not None
    
    def test_clear(self):
        """Test clearing stores."""
        self.rag.add("market_insights", ["Test"])
        self.rag.clear_all()
        
        stats = self.rag.get_stats()
        assert stats["market_insights"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

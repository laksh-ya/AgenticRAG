"""
Test KB Agent - Core novelty tests
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestKBAgent:
    """Test Knowledge Base Agent."""
    
    def setup_method(self):
        """Setup for each test."""
        from multi_rag.rag_manager import RAGManager
        from agents.kb_agent import KnowledgeBaseAgent
        
        self.rag = RAGManager()  # In-memory for tests
        self.kb = KnowledgeBaseAgent(self.rag)
    
    def test_pre_query_empty(self):
        """Test pre_query on empty KB."""
        result = self.kb.pre_query("AAPL", "2024-01-15")
        
        assert "context" in result
        assert "lessons" in result
        assert "decisions" in result
        assert isinstance(result["lessons"], list)
    
    def test_post_learn(self):
        """Test storing a decision."""
        ids = self.kb.post_learn(
            ticker="AAPL",
            date="2024-01-15",
            decision="BUY",
            reasoning="Strong fundamentals and bullish technicals",
            confidence=0.85
        )
        
        assert "decision_id" in ids
        assert ids["decision_id"] is not None
        
        # Verify it's in the KB
        stats = self.kb.get_stats()
        assert stats["trade_history"] >= 1
    
    def test_reflect(self):
        """Test learning from outcome."""
        lesson_id = self.kb.reflect(
            ticker="AAPL",
            date="2024-01-15",
            decision="BUY",
            reasoning="Strong fundamentals",
            actual_return=0.05  # 5% gain
        )
        
        assert lesson_id is not None
        
        # Verify lesson stored
        stats = self.kb.get_stats()
        assert stats["lessons_learned"] >= 1
    
    def test_full_flow(self):
        """Test full KB Agent flow."""
        # 1. Pre-query (empty)
        pre = self.kb.pre_query("MSFT", "2024-01-15")
        assert pre["context"]
        
        # 2. Post-learn
        self.kb.post_learn(
            ticker="MSFT",
            date="2024-01-15",
            decision="BUY",
            reasoning="Good earnings"
        )
        
        # 3. Pre-query again (should find context)
        pre2 = self.kb.pre_query("MSFT", "2024-01-20")
        # Context should now include the decision
        
        # 4. Reflect on outcome
        self.kb.reflect("MSFT", "2024-01-15", "BUY", "Good earnings", 0.08)
        
        # 5. Verify KB has grown
        stats = self.kb.get_stats()
        assert stats["trade_history"] >= 1
        assert stats["lessons_learned"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

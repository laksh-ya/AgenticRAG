"""
Knowledge Base Agent - THE CORE NOVELTY OF AGENTIC RAG

This agent ACTIVELY uses the RAG system:
1. QUERIES knowledge before analysis (pre_query)
2. STORES decisions after trading (post_learn)
3. LEARNS from outcomes (reflect)

This is what makes it "AGENTIC" RAG, not passive RAG.
"""
import os
import sys
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class KnowledgeBaseAgent:
    """
    THE CORE NOVELTY - An agent that actively uses and learns from RAG.
    
    Unlike passive RAG that just retrieves, this agent:
    - Queries BEFORE decisions to get historical context
    - Stores AFTER decisions for future reference
    - Learns from OUTCOMES to improve over time
    """
    
    def __init__(self, rag_manager, llm=None):
        """
        Args:
            rag_manager: RAGManager instance
            llm: Optional LLM for synthesis (uses simple formatting if None)
        """
        self.rag = rag_manager
        self.llm = llm
    
    # =========================================================================
    # CORE METHODS - The three key functions
    # =========================================================================
    
    def pre_query(self, ticker: str, date: str = None) -> Dict[str, Any]:
        """
        BEFORE ANALYSIS: Query RAG for historical context.
        
        Call this BEFORE analysts run to give them historical context.
        
        Args:
            ticker: Stock ticker (AAPL, MSFT, etc.)
            date: Optional date for context
        
        Returns:
            Dict with:
                - context: Synthesized context string
                - lessons: Past lessons for this ticker
                - decisions: Past decisions for this ticker
        """
        # Query all stores for this ticker
        query = f"Trading analysis and history for {ticker}"
        if date:
            query += f" around {date}"
        
        results = self.rag.query_all(query, n_per_store=3)
        
        # Format context for agents
        context = self._format_context(results, ticker)
        
        # Extract lessons
        lessons = []
        if "lessons_learned" in results:
            lessons = [r["text"][:200] for r in results["lessons_learned"]]
        
        # Extract past decisions
        decisions = []
        if "trade_history" in results:
            decisions = [r["text"][:200] for r in results["trade_history"]]
        
        return {
            "context": context,
            "lessons": lessons,
            "decisions": decisions,
            "raw": results
        }
    
    def post_learn(
        self,
        ticker: str,
        date: str,
        decision: str,
        reasoning: str,
        agent_outputs: Dict[str, str] = None,
        confidence: float = None
    ) -> Dict[str, str]:
        """
        AFTER DECISION: Store the decision in RAG.
        
        Call this AFTER trader makes a decision.
        
        Args:
            ticker: Stock ticker
            date: Analysis date
            decision: BUY/HOLD/SELL
            reasoning: Why this decision was made
            agent_outputs: Optional outputs from each agent
            confidence: Optional confidence score
        
        Returns:
            Dict with stored document IDs
        """
        # Store the decision
        decision_id = self.rag.store_decision(
            ticker=ticker,
            date=date,
            decision=decision,
            reasoning=reasoning,
            confidence=confidence
        )
        
        # Store insights from agent outputs
        insight_ids = []
        if agent_outputs:
            for agent_name, output in agent_outputs.items():
                if output and len(output) > 50:
                    insight = f"[{agent_name}] {output[:500]}"
                    iid = self.rag.store_insight(ticker, insight)
                    insight_ids.append(iid)
        
        return {
            "decision_id": decision_id,
            "insight_ids": insight_ids
        }
    
    def reflect(
        self,
        ticker: str,
        date: str,
        decision: str,
        reasoning: str,
        actual_return: float
    ) -> str:
        """
        LEARN FROM OUTCOME: When we know actual results, learn from them.
        
        This is a convenience wrapper. For richer reflections, use
        Explainability.learn_from_outcome() directly (it can use LLM
        to generate deeper analysis of what went wrong).
        
        Args:
            ticker: Stock ticker
            date: Original decision date
            decision: The decision that was made
            reasoning: Original reasoning
            actual_return: Actual return achieved (e.g. 0.05 = +5%)
        
        Returns:
            Lesson ID
        """
        was_correct = self._was_correct(decision, actual_return)
        lesson = self._generate_lesson(decision, actual_return, was_correct, reasoning)
        
        return self.rag.store_lesson(
            ticker=ticker,
            date=date,
            lesson=lesson,
            was_correct=was_correct,
            actual_return=actual_return
        )
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _format_context(self, results: Dict[str, List], ticker: str) -> str:
        """Format query results into readable context."""
        sections = []
        
        if results.get("market_insights"):
            sections.append("=== HISTORICAL INSIGHTS ===")
            for r in results["market_insights"][:2]:
                sections.append(f"• {r['text'][:300]}...")
        
        if results.get("trade_history"):
            sections.append("\n=== PAST DECISIONS ===")
            for r in results["trade_history"][:2]:
                sections.append(f"• {r['text'][:300]}...")
        
        if results.get("lessons_learned"):
            sections.append("\n=== LESSONS LEARNED ===")
            for r in results["lessons_learned"][:2]:
                sections.append(f"• {r['text'][:300]}...")
        
        if not sections:
            return f"No historical context found for {ticker}. This may be a new analysis."
        
        return "\n".join(sections)
    
    def _was_correct(self, decision: str, actual_return: float) -> bool:
        """Check if decision was correct."""
        decision = decision.upper()
        if decision == "BUY":
            return actual_return > 0
        elif decision == "SELL":
            return actual_return < 0
        else:
            return abs(actual_return) < 0.05
    
    def _generate_lesson(self, decision: str, ret: float, correct: bool, reasoning: str = "") -> str:
        """Generate a lesson from the outcome."""
        if correct:
            return (
                f"SUCCESSFUL {decision} ({ret:+.2%} return). "
                f"Analysis correctly identified direction. "
                f"Trust similar signals in future. "
                f"Reasoning: {reasoning[:200]}"
            )
        else:
            return (
                f"FAILED {decision} ({ret:+.2%} return). "
                f"Analysis missed key factors — be more cautious "
                f"with similar setups. "
                f"Original reasoning: {reasoning[:200]}"
            )
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_stats(self) -> Dict[str, int]:
        """Get knowledge base statistics."""
        return self.rag.get_stats()
    
    def add_custom_knowledge(self, ticker: str, knowledge: str) -> str:
        """Add custom knowledge to the base."""
        return self.rag.store_insight(ticker, knowledge)

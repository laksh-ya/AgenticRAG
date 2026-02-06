"""
Explainability - The learning loop that makes this an AGENTIC RAG system.

Two-phase design:
─────────────────────────────────────────────────────────────────────

PHASE 1: SNAPSHOT (automatic, runs at end of every analysis)
  → Called by the graph's "explainability" node right after Trader
  → Generates a structured report of WHAT each agent said and WHY
  → Stores it in RAG as a "market_insights" document
  → This is ALWAYS stored, regardless of whether you ever check the outcome

PHASE 2: OUTCOME LEARNING (manual, when you know what actually happened)
  → Called later via:
      - app_kb_train.py "Teach Outcomes" tab (enter return % in UI)
      - TradingGraph.learn_from_outcome() (programmatic)
      - Future: automated via paper trading / brokerage API
  → Compares decision vs actual return
  → Generates a LESSON: "BUY was wrong because X" or "SELL was right"
  → Stores the lesson in RAG as a "lessons_learned" document
  → Future analyses retrieve these lessons via KB Agent pre_query

This is the NOVELTY: the RAG doesn't just store static docs — it builds
institutional memory from its own successes and failures.
─────────────────────────────────────────────────────────────────────
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime


class Explainability:
    """Generates analysis snapshots and learns from outcomes."""

    def __init__(self, rag_manager, llm=None):
        self.rag = rag_manager
        self.llm = llm

    # ==================================================================
    # PHASE 1: Snapshot (automatic after every analysis)
    # ==================================================================

    def generate_report(
        self,
        ticker: str,
        date: str,
        decision: str,
        confidence: float,
        agent_outputs: Dict[str, str],
        reasoning: str = "",
        portfolio: list = None,
    ) -> str:
        """
        Build a structured explainability report from all agent outputs.
        Called automatically by the graph after the Trader node.
        """
        lines = [
            "=" * 70,
            "EXPLAINABILITY REPORT",
            "=" * 70,
            f"Ticker:     {ticker}",
            f"Date:       {date}",
            f"Decision:   {decision}",
            f"Confidence: {confidence:.1%}",
            f"Generated:  {datetime.now().isoformat()}",
            "=" * 70,
            "",
        ]

        if portfolio:
            matching = [h for h in portfolio if h.get("ticker") == ticker]
            if matching:
                h = matching[0]
                lines.append("## Current Position")
                lines.append(
                    f"  Holding {h['shares']} shares @ ${h['avg_price']:.2f} avg"
                )
                lines.append("")

        section_order = [
            ("fundamentals_report", "Fundamentals Analysis"),
            ("market_report", "Market / Technical Analysis"),
            ("news_report", "News Analysis"),
            ("social_report", "Social Media Sentiment"),
            ("bull_argument", "Bull Researcher"),
            ("bear_argument", "Bear Researcher"),
            ("research_summary", "Research Manager Synthesis"),
            ("risk_assessment", "Risk Assessment"),
        ]

        for key, title in section_order:
            content = agent_outputs.get(key, "")
            if content:
                lines.append(f"## {title}")
                lines.append(content)
                lines.append("")

        if reasoning:
            lines.append("## Trader's Final Reasoning")
            lines.append(reasoning)
            lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)

    def store_report(self, ticker: str, date: str, report: str) -> str:
        """Store the snapshot in RAG. Returns document ID."""
        return self.rag.store_insight(
            ticker=ticker,
            insight=report,
            metadata={
                "type": "explainability_report",
                "date": date,
                "phase": "snapshot",
            },
        )

    # ==================================================================
    # PHASE 2: Outcome Learning (manual, called later)
    # ==================================================================

    def learn_from_outcome(
        self,
        ticker: str,
        date: str,
        decision: str,
        reasoning: str,
        actual_return: float,
    ) -> str:
        """
        Feed back actual returns to teach the RAG system.

        Args:
            ticker: "AAPL"
            date: "2024-01-15" (the date of the original decision)
            decision: "BUY" / "SELL" / "HOLD"
            reasoning: original reasoning (so the lesson can reference it)
            actual_return: e.g. 0.05 for +5%, -0.03 for -3%

        Returns:
            Document ID of the stored lesson.
        """
        was_correct = self._evaluate(decision, actual_return)

        # Build a detailed lesson
        outcome_emoji = "✅" if was_correct else "❌"
        lesson_parts = [
            f"{outcome_emoji} OUTCOME for {ticker} ({date})",
            f"Decision: {decision}",
            f"Actual Return: {actual_return:+.2%}",
            f"Result: {'CORRECT' if was_correct else 'INCORRECT'}",
            "",
        ]

        if was_correct:
            lesson_parts.append(
                f"The {decision} decision was validated by a {actual_return:+.2%} return. "
                f"The analysis correctly identified the market direction."
            )
        else:
            lesson_parts.append(
                f"The {decision} decision was WRONG — actual return was {actual_return:+.2%}. "
                f"Key factors were missed or misweighed."
            )

        # Include a snippet of original reasoning for context
        if reasoning:
            lesson_parts.append("")
            lesson_parts.append(f"Original reasoning snippet: {reasoning[:300]}")

        # If we have an LLM, generate a richer reflection
        if self.llm:
            try:
                reflection = self._llm_reflect(
                    ticker, date, decision, reasoning, actual_return, was_correct
                )
                lesson_parts.append("")
                lesson_parts.append(f"AI Reflection: {reflection}")
            except Exception:
                pass  # LLM reflection is optional

        lesson = "\n".join(lesson_parts)

        return self.rag.store_lesson(
            ticker=ticker,
            date=date,
            lesson=lesson,
            was_correct=was_correct,
            actual_return=actual_return,
        )

    def _evaluate(self, decision: str, actual_return: float) -> bool:
        """Was the decision correct given actual returns?"""
        d = decision.upper()
        if d == "BUY":
            return actual_return > 0
        elif d == "SELL":
            return actual_return < 0
        else:  # HOLD
            return abs(actual_return) < 0.05

    def _llm_reflect(
        self, ticker, date, decision, reasoning, actual_return, was_correct
    ) -> str:
        """Ask the LLM to generate a richer reflection (optional)."""
        prompt = (
            f"You are reviewing a past trading decision.\n\n"
            f"Ticker: {ticker}, Date: {date}\n"
            f"Decision: {decision}, Return: {actual_return:+.2%}\n"
            f"Outcome: {'CORRECT' if was_correct else 'INCORRECT'}\n\n"
            f"Original reasoning:\n{reasoning[:500]}\n\n"
            f"Write 2-3 sentences analyzing what went right or wrong "
            f"and what to watch for next time. Be specific."
        )
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

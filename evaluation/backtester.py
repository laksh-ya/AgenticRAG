"""
Backtester - Multi-day rolling evaluation
"""
import os
import sys
from typing import Dict, Any, List
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Backtester:
    """
    Run analysis over multiple days and evaluate.
    """
    
    def __init__(self):
        from graphs.trading_graph import TradingGraph
        self.trading = TradingGraph()
    
    def run_single(self, ticker: str, date: str, portfolio: list = None) -> Dict[str, Any]:
        """Run analysis for a single day.
        
        Args:
            portfolio: Holdings list. Pass [] for a fresh-entry (no holdings)
                       backtest. Pass None to use the system default preset.
        """
        try:
            result = self.trading.run(ticker, date, portfolio=portfolio)
            return {
                "ticker": ticker,
                "date": date,
                "decision": result["decision"],
                "confidence": result["confidence"],
                "reasoning": result["reasoning"][:500],
                "success": True
            }
        except Exception as e:
            return {
                "ticker": ticker,
                "date": date,
                "decision": "ERROR",
                "confidence": 0.0,
                "reasoning": str(e),
                "success": False
            }
    
    def run_backtest(self, ticker: str, end_date: str, days: int = 30, portfolio: list = None) -> List[Dict]:
        """Run backtest over multiple days.
        
        Args:
            portfolio: Holdings list. Pass [] for fresh-entry backtests.
                       Pass None to use the system default preset.
        """
        results = []
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        for i in range(days):
            date = (end - timedelta(days=days - i - 1)).strftime("%Y-%m-%d")
            result = self.run_single(ticker, date, portfolio=portfolio)
            results.append(result)
        
        return results
    
    def summarize(self, results: List[Dict]) -> Dict[str, Any]:
        """Summarize backtest results."""
        successful = [r for r in results if r["success"]]
        
        buy_count = sum(1 for r in successful if r["decision"] == "BUY")
        sell_count = sum(1 for r in successful if r["decision"] == "SELL")
        hold_count = sum(1 for r in successful if r["decision"] == "HOLD")
        
        avg_confidence = sum(r["confidence"] for r in successful) / len(successful) if successful else 0
        
        return {
            "total_days": len(results),
            "successful_days": len(successful),
            "failed_days": len(results) - len(successful),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "hold_count": hold_count,
            "avg_confidence": avg_confidence,
        }

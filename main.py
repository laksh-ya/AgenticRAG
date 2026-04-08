"""
KARMA - Main Entry Point
Knowledge-Aware Reinforced Multi-Agent Framework for Autonomous Financial Investment Decision-Making
Simple example usage for intraday trading analysis
"""
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from karma.graph.trading_graph import TradingGraph
from karma.config import SUPPORTED_TICKERS, PRESET_PORTFOLIOS, DEFAULT_PORTFOLIO_KEY


def main():
    """Run an intraday trading analysis."""
    print("=" * 60)
    print("KARMA — Intraday Investment Decision System")
    print("Knowledge-Aware Reinforced Multi-Agent Framework")
    print("=" * 60)

    # Parse optional --portfolio flag (e.g. --portfolio heavy_tech)
    portfolio_key = DEFAULT_PORTFOLIO_KEY
    if "--portfolio" in sys.argv:
        idx = sys.argv.index("--portfolio")
        if idx + 1 < len(sys.argv) and sys.argv[idx + 1] in PRESET_PORTFOLIOS:
            portfolio_key = sys.argv[idx + 1]
        else:
            valid = ", ".join(PRESET_PORTFOLIOS.keys())
            print(f"Invalid portfolio key. Valid options: {valid}")
            return

    portfolio = PRESET_PORTFOLIOS[portfolio_key]["holdings"]
    portfolio_label = PRESET_PORTFOLIOS[portfolio_key]["label"]

    # Create the trading graph
    print("\nInitializing system...")
    trading = TradingGraph()

    # Show KB stats
    stats = trading.get_kb_stats()
    print(f"Knowledge Base: {stats}")

    # Run analysis
    ticker = "AAPL"
    date = "2024-01-15"

    print(f"\nAnalyzing {ticker} for {date}...")
    print(f"Portfolio: {portfolio_label}")
    print("-" * 40)

    result = trading.run(ticker, date, portfolio=portfolio)

    # Display results
    print(f"\n{'=' * 60}")
    print(f"RESULT: {result['decision']}")
    print(f"Confidence: {result['confidence']:.1%}")
    print(f"{'=' * 60}")
    print(f"\nReasoning:\n{result['reasoning']}")

    # Explainability report
    if result.get("explainability_report"):
        print(f"\n{result['explainability_report']}")

    # Save result
    path = trading.save_result(result)
    print(f"\nResult saved to: {path}")

    # Show updated KB stats
    stats = trading.get_kb_stats()
    print(f"\nKnowledge Base (after): {stats}")

    return result


if __name__ == "__main__":
    main()

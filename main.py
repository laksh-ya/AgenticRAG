"""
AgenticRAG - Main Entry Point
Simple example usage
"""
from graphs.trading_graph import TradingGraph
from preferences import SUPPORTED_TICKERS


def main():
    """Run a trading analysis."""
    print("=" * 60)
    print("AgenticRAG - Investment Decision System")
    print("=" * 60)

    # Create the trading graph
    print("\nInitializing system...")
    trading = TradingGraph()

    # Show KB stats
    stats = trading.get_kb_stats()
    print(f"Knowledge Base: {stats}")

    # Run analysis
    ticker = "AAPL"
    date = "2024-01-15"

    # Optional: provide portfolio for risk-aware analysis
    portfolio = [
        {"ticker": "AAPL", "shares": 50, "avg_price": 178.50},
        {"ticker": "MSFT", "shares": 30, "avg_price": 365.00},
    ]

    print(f"\nAnalyzing {ticker} for {date}...")
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

"""
Portfolio Utilities — Builds a formatted portfolio summary with live prices,
allocation percentages, PnL, and concentration warnings.
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

CONCENTRATION_THRESHOLD = 0.25  # 25%


def _fetch_current_price(ticker: str, fallback_price: float) -> float:
    """Fetch the latest price via yfinance; fall back to avg_price on failure."""
    try:
        import yfinance as yf
        data = yf.Ticker(ticker).history(period="1d")
        if data.empty:
            logger.warning("yfinance returned no data for %s, using fallback $%.2f", ticker, fallback_price)
            return fallback_price
        return float(data["Close"].iloc[-1])
    except Exception as e:
        logger.warning("yfinance fetch failed for %s (%s), using fallback $%.2f", ticker, e, fallback_price)
        return fallback_price


def build_portfolio_summary(holdings: List[Dict], target_ticker: str) -> str:
    """
    Build a human-readable portfolio summary string ready for LLM prompts.

    Parameters
    ----------
    holdings : list of dicts with keys ticker, shares, avg_price
    target_ticker : the ticker currently being analysed

    Returns
    -------
    str — formatted summary including per-holding stats, total value,
          target-ticker context, and concentration warnings.
    """
    # Handle empty / fresh-entry portfolio
    if not holdings:
        return (
            "PORTFOLIO SUMMARY\n"
            "No current holdings — fresh account, full capital available for new positions."
        )

    # Filter to holdings with shares > 0
    active = [h for h in holdings if h.get("shares", 0) > 0]
    if not active:
        return (
            "PORTFOLIO SUMMARY\n"
            "No current holdings — fresh account, full capital available for new positions."
        )

    # Fetch current prices and compute per-holding metrics
    enriched = []
    for h in active:
        ticker = h["ticker"]
        shares = h["shares"]
        avg_price = h["avg_price"]
        current_price = _fetch_current_price(ticker, avg_price)
        market_value = shares * current_price
        cost_basis = shares * avg_price
        unrealized_pnl = market_value - cost_basis
        pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis else 0.0
        enriched.append({
            "ticker": ticker,
            "shares": shares,
            "avg_price": avg_price,
            "current_price": current_price,
            "market_value": market_value,
            "cost_basis": cost_basis,
            "unrealized_pnl": unrealized_pnl,
            "pnl_pct": pnl_pct,
        })

    total_value = sum(e["market_value"] for e in enriched)

    # Compute allocation %
    for e in enriched:
        e["allocation_pct"] = (e["market_value"] / total_value * 100) if total_value else 0.0

    # Build the text
    lines = ["PORTFOLIO SUMMARY"]
    lines.append(f"Total Value: ${total_value:,.2f}")
    lines.append("Holdings:")
    for e in enriched:
        pnl_sign = "+" if e["unrealized_pnl"] >= 0 else ""
        lines.append(
            f"  {e['ticker']}: {e['shares']:.0f} shares @ ${e['current_price']:.2f} current "
            f"| ${e['market_value']:,.2f} value | {e['allocation_pct']:.1f}% of portfolio "
            f"| {pnl_sign}${e['unrealized_pnl']:,.2f} unrealized ({pnl_sign}{e['pnl_pct']:.1f}%)"
        )

    # Target ticker context
    target_holding = next((e for e in enriched if e["ticker"] == target_ticker), None)
    lines.append("")
    lines.append(f"TARGET TICKER CONTEXT ({target_ticker}):")
    if target_holding:
        lines.append(
            f"  Current position: {target_holding['shares']:.0f} shares worth "
            f"${target_holding['market_value']:,.2f} ({target_holding['allocation_pct']:.1f}% of portfolio)"
        )
    else:
        lines.append(f"  No existing position in {target_ticker} — this would be a new entry.")

    # Concentration warnings (check every holding)
    warnings = []
    for e in enriched:
        if e["allocation_pct"] / 100 >= CONCENTRATION_THRESHOLD:
            warnings.append(
                f"  ⚠️ CONCENTRATION WARNING: {e['ticker']} is {e['allocation_pct']:.1f}% "
                f"of portfolio — above {CONCENTRATION_THRESHOLD:.0%} threshold"
            )
    if warnings:
        for w in warnings:
            lines.append(w)

    return "\n".join(lines)

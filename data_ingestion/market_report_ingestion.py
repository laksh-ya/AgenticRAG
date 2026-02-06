import yfinance as yf
import json, sys
import numpy as np
from config import COMPANY_MAP

# -----------------------------
# Sector normalization + ETF map
# -----------------------------
SECTOR_ETF_MAP = {
    "Information Technology": "XLK",
    "Technology": "XLK",
    "Communication Services": "XLC",
    "Consumer Discretionary": "XLY",
    "Consumer Cyclical": "XLY"
}

# -----------------------------
# Argument check
# -----------------------------
if len(sys.argv) < 2:
    print("Usage: python market_report_ingestion.py <TICKER>")
    sys.exit(1)

symbol = sys.argv[1].upper()
company = COMPANY_MAP.get(symbol)

if not company:
    print("Company not supported")
    sys.exit(1)

# -----------------------------
# 1️⃣ Stock performance (last 3 months)
# -----------------------------
stock = yf.Ticker(symbol)
hist = stock.history(period="3mo")

price_start = hist["Close"].iloc[0]
price_end = hist["Close"].iloc[-1]
price_change_pct = round(((price_end - price_start) / price_start) * 100, 2)

stock_trend = "bullish" if price_change_pct > 0 else "bearish"

# Volatility
daily_returns = hist["Close"].pct_change().dropna()
volatility = np.std(daily_returns) * np.sqrt(252)

if volatility > 0.35:
    volatility_signal = "high"
elif volatility > 0.20:
    volatility_signal = "moderate"
else:
    volatility_signal = "low"

# -----------------------------
# 2️⃣ Sector performance via ETF (FIXED)
# -----------------------------
info = stock.info
raw_sector = info.get("sector")

sector = raw_sector if raw_sector else "Unknown"
etf_symbol = SECTOR_ETF_MAP.get(sector)

sector_return = None
sector_signal = "unknown"
relative_performance = "unknown"

if etf_symbol:
    etf = yf.Ticker(etf_symbol)
    etf_hist = etf.history(period="3mo")

    etf_start = etf_hist["Close"].iloc[0]
    etf_end = etf_hist["Close"].iloc[-1]
    sector_return = round(((etf_end - etf_start) / etf_start) * 100, 2)

    sector_signal = "bullish" if sector_return > 0 else "bearish"

    if price_change_pct > sector_return:
        relative_performance = "outperforming"
    else:
        relative_performance = "underperforming"

# -----------------------------
# 3️⃣ Market risk (VIX)
# -----------------------------
vix_avg = round(
    yf.Ticker("^VIX").history(period="3mo")["Close"].mean(), 2
)

if vix_avg > 25:
    risk_level = "high"
elif vix_avg > 18:
    risk_level = "moderate"
else:
    risk_level = "low"

# -----------------------------
# 4️⃣ Investment decision
# -----------------------------
if price_change_pct < -5:
    investment_view = "unfavorable"
elif price_change_pct < 0:
    investment_view = "neutral"
else:
    investment_view = "favorable"

decision_rationale = (
    "Investment view is based on recent stock momentum, "
    "sector ETF performance, and overall market risk."
)

confidence_score = round(
    0.4 * (1 if stock_trend == "bullish" else 0) +
    0.3 * (1 if sector_signal == "bullish" else 0) +
    0.3 * (1 if risk_level == "low" else 0),
    2
)

# -----------------------------
# 5️⃣ Output
# -----------------------------
output = {
    "company": company,
    "ticker": symbol,
    "time_window": "last_3_months",
    "stock_performance": {
        "price_change_percent": price_change_pct,
        "trend": stock_trend,
        "volatility": volatility_signal
    },
    "sector_performance": {
        "sector": sector,
        "sector_etf": etf_symbol,
        "sector_3m_return_percent": sector_return,
        "sector_signal": sector_signal,
        "relative_to_sector": relative_performance
    },
    "risk_context": {
        "vix_average": vix_avg,
        "risk_level": risk_level
    },
    "investment_view": investment_view,
    "decision_rationale": decision_rationale,
    "confidence_score": confidence_score,
    "sources": ["Yahoo Finance"]
}

with open(f"output/market_report_{symbol}.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=4)

print(f"✅ market_report_{symbol}.json generated (sector FIXED)")

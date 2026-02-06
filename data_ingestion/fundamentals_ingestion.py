import requests, json, sys
import yfinance as yf
from config import ALPHA_VANTAGE_API_KEY, COMPANY_MAP

if len(sys.argv) < 2:
    print("Usage: python fundamentals_ingestion.py <TICKER>")
    sys.exit(1)

symbol = sys.argv[1].upper()
company = COMPANY_MAP.get(symbol)

if not company:
    print("Company not supported")
    sys.exit(1)

# -----------------------------
# Alpha Vantage (basic snapshot)
# -----------------------------
BASE_URL = "https://www.alphavantage.co/query"
av_data = requests.get(BASE_URL, params={
    "function": "OVERVIEW",
    "symbol": symbol,
    "apikey": ALPHA_VANTAGE_API_KEY
}).json()

# -----------------------------
# Yahoo Finance (deep metrics)
# -----------------------------
stock = yf.Ticker(symbol)
info = stock.info
financials = stock.financials
cashflow = stock.cashflow

# -----------------------------
# Build investment-grade report
# -----------------------------
output = {
    "company": company,
    "ticker": symbol,
    "as_of": av_data.get("LatestQuarter"),
    "data_sources": {
        "primary": "Alpha Vantage",
        "fallback": "Yahoo Finance"
    },
    "fundamentals": {
        "valuation": {
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "price_to_book": info.get("priceToBook"),
            "peg_ratio": info.get("pegRatio"),
            "valuation_signal": "fair" if info.get("trailingPE", 0) < 35 else "expensive"
        },
        "profitability": {
            "eps": info.get("trailingEps"),
            "operating_margin": info.get("operatingMargins"),
            "net_margin": info.get("profitMargins"),
            "roe": info.get("returnOnEquity"),
            "profitability_signal": "strong" if info.get("profitMargins", 0) > 0.2 else "weak"
        },
        "financial_health": {
            "free_cash_flow": info.get("freeCashflow"),
            "debt_to_equity": info.get("debtToEquity"),
            "cash_on_hand": info.get("totalCash"),
            "health_signal": "very strong" if info.get("debtToEquity", 1) < 0.5 else "moderate"
        },
        "growth": {
            "revenue_growth_yoy": info.get("revenueGrowth"),
            "eps_growth_yoy": info.get("earningsGrowth"),
            "growth_signal": "strong" if info.get("revenueGrowth", 0) > 0.1 else "moderate"
        }
    }
}

# -----------------------------
# Save output
# -----------------------------
with open(f"output/fundamentals_{symbol}.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=4)

print(f"✅ fundamentals_{symbol}.json generated (investment-grade)")

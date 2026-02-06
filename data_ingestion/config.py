import os
from datetime import datetime, timedelta

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

COMPANY_MAP = {
    "AAPL": "Apple Inc",
    "GOOGL": "Google",
    "NVDA": "Nvidia",
    "MSFT": "Microsoft",
    "AMZN": "Amazon"
}

# last 3 months window
THREE_MONTHS_AGO = datetime.now() - timedelta(days=90)


INVESTMENT_KEYWORDS = [
    "earnings", "revenue", "profit", "guidance",
    "analyst", "upgrade", "downgrade", "price target",
    "buy", "sell", "hold",
    "institutional", "stake", "shares",
    "quarter", "fiscal",
    "dividend", "valuation",
    "acquires", "acquisition", "merger",
    "ipo", "buyback", "repurchase"
]
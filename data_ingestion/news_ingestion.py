import requests
import json
import sys
import os
from datetime import datetime, timedelta
import feedparser

from config import COMPANY_MAP, ALPHA_VANTAGE_API_KEY

# ---------------- INPUT ----------------
if len(sys.argv) < 2:
    print("Usage: python news_ingestion.py <TICKER>")
    sys.exit(1)

symbol = sys.argv[1].upper()
company = COMPANY_MAP.get(symbol)

if not company:
    print("❌ Company not supported")
    sys.exit(1)

print(f"Fetching INVESTMENT news for {company}")

# ---------------- TIME WINDOW ----------------
today = datetime.utcnow()
three_months_ago = today - timedelta(days=90)

# ---------------- KEYWORDS ----------------
INCLUDE_TERMS = [
    "stock", "shares", "earnings", "revenue", "profit",
    "analyst", "rating", "upgrade", "downgrade",
    "price target", "valuation", "buy", "sell", "hold",
    "lawsuit", "fine", "settlement",
    "market cap", "growth", "guidance", "forecast",
    "institutional", "investor", "fund", "portfolio",
    "quarter", "fiscal", "results", "outlook"
]

EXCLUDE_TERMS = [
    "conference", "summit", "agenda",
    "appoints", "names chief", "unveils",
    "raises", "funding", "series a", "series b",
    "event", "expo", "webinar", "hiring",
    "etf", "gold", "crypto", "bitcoin"
]

COMPANY_TERMS = [
    symbol.lower(),
    company.lower(),
    company.lower().split()[0]
]

# ---------------- SENTIMENT LEXICON ----------------
BULLISH_TERMS = [
    # ---- analyst ratings & recommendations ----
    "buy", "strong buy", "outperform", "overweight",
    "upgrade", "upgraded", "initiated at buy",
    "positive rating", "bullish rating",

    # ---- valuation language ----
    "undervalued", "too cheap", "cheap valuation",
    "attractive valuation", "compelling valuation",
    "discounted", "trades below intrinsic value",
    "margin of safety",

    # ---- price targets ----
    "price target", "raised target", "target raised",
    "price target raised", "upside potential",
    "implied upside",

    # ---- earnings & financial performance ----
    "earnings beat", "beat estimates", "beat expectations",
    "revenue beat", "profit beat",
    "strong earnings", "record earnings",
    "revenue growth", "sales growth",
    "profit growth", "margin expansion",
    "operating leverage", "strong margins",
    "cash flow", "free cash flow growth",
    "fcf growth",

    # ---- guidance & outlook ----
    "strong guidance", "raised guidance",
    "positive outlook", "optimistic outlook",
    "improving outlook", "long-term growth",
    "accelerating growth",

    # ---- investor & institutional behavior ----
    "institutional buying", "fund buying",
    "hedge fund buying", "accumulates",
    "loads up", "buys", "added shares",
    "stake increase", "position increased",
    "increased holding",

    # ---- balance sheet strength ----
    "strong balance sheet", "low debt",
    "net cash position", "high liquidity",

    # ---- momentum & market behavior ----
    "rally", "surge", "jump", "gains",
    "uptrend", "breakout", "record high",
    "new highs", "positive momentum",
    "bullish momentum",

    # ---- strategic & competitive ----
    "market leader", "dominant position",
    "competitive advantage", "pricing power",
    "strong demand", "robust demand",

    # ---- corporate actions ----
    "share buyback", "buyback program",
    "dividend increase", "capital return",

    # ---- risk resolution ----
    "lawsuit resolved", "settlement reached",
    "regulatory approval", "approval granted",

    # ---- explicit sentiment ----
    "bullish", "very bullish"
]


BEARISH_TERMS = [
    # ---- analyst ratings & recommendations ----
    "sell", "strong sell", "underperform",
    "downgrade", "downgraded", "reduced rating",
    "negative rating", "bearish rating",

    # ---- valuation language ----
    "overvalued", "expensive valuation",
    "stretched valuation", "fully valued",
    "limited upside",

    # ---- price targets ----
    "price target cut", "lowered target",
    "target cut", "price target lowered",
    "downside risk",

    # ---- earnings & financial performance ----
    "earnings miss", "miss estimates",
    "miss expectations", "revenue miss",
    "profit miss",
    "weak earnings", "disappointing earnings",
    "slowing growth", "declining revenue",
    "profit decline", "margin pressure",
    "margin compression",
    "cost surge", "rising costs",
    "cash burn", "negative cash flow",

    # ---- guidance & outlook ----
    "weak guidance", "lowered guidance",
    "cut guidance", "cautious outlook",
    "uncertain outlook", "demand slowdown",

    # ---- investor & institutional behavior ----
    "institutional selling", "fund selling",
    "hedge fund selling", "stake reduction",
    "position reduced", "trimmed stake",
    "fund exits", "sold shares",

    # ---- balance sheet risks ----
    "high debt", "leverage concerns",
    "liquidity concerns", "debt burden",

    # ---- momentum & market behavior ----
    "selloff", "plunge", "drop", "fall",
    "decline", "slides", "tanks",
    "downtrend", "breakdown",
    "negative momentum",

    # ---- strategic & competitive ----
    "loss of market share", "competitive pressure",
    "pricing pressure", "weak demand",

    # ---- corporate actions ----
    "dividend cut", "suspends dividend",
    "dilution", "equity issuance",

    # ---- legal & regulatory ----
    "lawsuit", "regulatory probe",
    "investigation", "antitrust",
    "fine imposed", "penalty",

    # ---- macro / risk ----
    "economic slowdown", "recession fears",
    "rate hike impact",

    # ---- explicit sentiment ----
    "bearish", "very bearish"
]


def compute_sentiment(text: str):
    text = text.lower()
    bull = sum(text.count(w) for w in BULLISH_TERMS)
    bear = sum(text.count(w) for w in BEARISH_TERMS)

    score = bull - bear

    if score >= 1:
        return "Bullish", min(score / 6, 1.0)
    elif score <= -1:
        return "Bearish", max(score / 6, -1.0)
    else:
        return "Neutral", score / 6

articles = []

# =====================================================
# 1️⃣ ALPHA VANTAGE (PRIMARY)
# =====================================================
try:
    av_url = "https://www.alphavantage.co/query"
    av_params = {
        "function": "NEWS_SENTIMENT",
        "tickers": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    av_data = requests.get(av_url, params=av_params, timeout=10).json()
    feed = av_data.get("feed", [])

    for item in feed:
        try:
            published = datetime.strptime(item["time_published"], "%Y%m%dT%H%M%S")
        except:
            continue

        if published < three_months_ago:
            continue

        text = (item.get("title", "") + " " + item.get("summary", "")).lower()

        if not any(t in text for t in INCLUDE_TERMS):
            continue
        if any(t in text for t in EXCLUDE_TERMS):
            continue
        if not any(t in text for t in COMPANY_TERMS):
            continue

        sentiment = item.get("overall_sentiment_label")
        score = item.get("overall_sentiment_score")

        if sentiment is None or score is None:
            sentiment, score = compute_sentiment(text)

        articles.append({
            "source": "Alpha Vantage",
            "headline": item.get("title"),
            "summary": item.get("summary"),
            "sentiment": sentiment,
            "sentiment_score": round(score, 3),
            "date": item.get("time_published")
        })

except Exception:
    pass

# =====================================================
# 2️⃣ YAHOO FINANCE RSS (FALLBACK)
# =====================================================
if len(articles) == 0:
    print("Alpha Vantage unavailable → using Yahoo Finance RSS")

    rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    feed = feedparser.parse(rss_url)

    for entry in feed.entries:
        if not hasattr(entry, "published_parsed"):
            continue

        published = datetime(*entry.published_parsed[:6])
        if published < three_months_ago:
            continue

        text = (entry.title + " " + entry.summary).lower()

        if not any(t in text for t in INCLUDE_TERMS):
            continue
        if any(t in text for t in EXCLUDE_TERMS):
            continue
        if not any(t in text for t in COMPANY_TERMS):
            continue

        sentiment, score = compute_sentiment(text)

        articles.append({
            "source": "Yahoo Finance",
            "headline": entry.title,
            "summary": entry.summary,
            "sentiment": sentiment,
            "sentiment_score": round(score, 3),
            "date": published.strftime("%Y%m%dT%H%M%S")
        })

# ---------------- OUTPUT ----------------
os.makedirs("output", exist_ok=True)

output = {
    "company": company,
    "ticker": symbol,
    "time_window": "last_3_months",
    "article_count": len(articles),
    "articles": articles,
    "note": "Company-specific investment news with rule-based financial sentiment scoring"
}

file_path = f"output/investment_news_{symbol}.json"
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=4)

print(f"✅ {file_path} generated with {len(articles)} INVESTMENT articles")

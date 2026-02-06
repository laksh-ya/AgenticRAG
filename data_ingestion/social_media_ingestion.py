import requests
import json
import sys
import feedparser
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from config import COMPANY_MAP

# ================= CLI =================
if len(sys.argv) < 2:
    print("Usage: python social_media_ingestion.py <TICKER>")
    sys.exit(1)

symbol = sys.argv[1].upper()
company = COMPANY_MAP.get(symbol)

if not company:
    print("Unsupported ticker")
    sys.exit(1)

# ================= CONFIG =================
analyzer = SentimentIntensityAnalyzer()
THREE_MONTHS_AGO = datetime.utcnow() - timedelta(days=90)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Investment Research Bot)"
}

FINANCE_SUBREDDITS = {
    "stocks", "investing", "stockmarket",
    "options", "securityanalysis",
    "valueinvesting", "wallstreetbets"
}

INVESTMENT_KEYWORDS = [
    "stock", "shares", "earnings", "revenue", "profit",
    "loss", "guidance", "valuation", "price target",
    "upgrade", "downgrade", "buy", "sell", "hold",
    "bullish", "bearish", "institutional",
    "results", "forecast", "outperform", "underperform"
]

# ================= HELPERS =================
def is_investment_text(text):
    text = text.lower()
    return any(k in text for k in INVESTMENT_KEYWORDS)

def analyze_sentiment(text):
    score = analyzer.polarity_scores(text)["compound"]
    if score >= 0.05:
        return "Bullish", round(score, 3)
    elif score <= -0.05:
        return "Bearish", round(score, 3)
    return "Neutral", round(score, 3)

posts = []

# ================= REDDIT (SAFE) =================
print(f"Fetching Reddit investor sentiment for {company}")

try:
    reddit_url = f"https://www.reddit.com/search.json?q={symbol}&limit=100"
    r = requests.get(reddit_url, headers=HEADERS, timeout=15)

    if r.status_code == 200 and "application/json" in r.headers.get("Content-Type", ""):
        data = r.json()
        for item in data.get("data", {}).get("children", []):
            d = item["data"]
            created = datetime.utcfromtimestamp(d.get("created_utc", 0))
            title = d.get("title", "")
            subreddit = d.get("subreddit", "").lower()

            if (
                created >= THREE_MONTHS_AGO
                and subreddit in FINANCE_SUBREDDITS
                and is_investment_text(title)
            ):
                sent, score = analyze_sentiment(title)
                posts.append({
                    "platform": "reddit",
                    "source": subreddit,
                    "text": title,
                    "sentiment": sent,
                    "sentiment_score": score,
                    "date": created.strftime("%Y-%m-%d")
                })
    else:
        print("⚠️ Reddit returned non-JSON or blocked")

except Exception as e:
    print(f"⚠️ Reddit skipped due to error: {e}")

# ================= STOCKTWITS =================
print(f"Fetching StockTwits investor sentiment for {company}")

try:
    stocktwits_url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
    r = requests.get(stocktwits_url, timeout=10)

    if r.status_code == 200:
        data = r.json()
        for msg in data.get("messages", []):
            created = datetime.strptime(msg["created_at"][:10], "%Y-%m-%d")
            body = msg.get("body", "")

            if created >= THREE_MONTHS_AGO and is_investment_text(body):
                sent, score = analyze_sentiment(body)
                posts.append({
                    "platform": "stocktwits",
                    "source": "StockTwits",
                    "text": body,
                    "sentiment": sent,
                    "sentiment_score": score,
                    "date": created.strftime("%Y-%m-%d")
                })
except Exception as e:
    print(f"⚠️ StockTwits skipped: {e}")

# ================= YAHOO FINANCE =================
print(f"Fetching Yahoo Finance investment news for {company}")

rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
feed = feedparser.parse(rss_url)

for entry in feed.entries:
    published = datetime(*entry.published_parsed[:6])
    headline = entry.title
    summary = entry.summary if hasattr(entry, "summary") else ""

    if published >= THREE_MONTHS_AGO and is_investment_text(headline + " " + summary):
        sent, score = analyze_sentiment(headline + " " + summary)
        posts.append({
            "platform": "yahoo_finance",
            "source": "Yahoo Finance",
            "text": headline,
            "sentiment": sent,
            "sentiment_score": score,
            "date": published.strftime("%Y-%m-%d")
        })

# ================= SUMMARY =================
sentiment_summary = {"Bullish": 0, "Neutral": 0, "Bearish": 0}
for p in posts:
    sentiment_summary[p["sentiment"]] += 1

# ================= OUTPUT =================
output = {
    "company": company,
    "ticker": symbol,
    "time_window": "last_3_months",
    "sources": ["reddit", "stocktwits", "yahoo_finance"],
    "post_count": len(posts),
    "sentiment_summary": sentiment_summary,
    "posts": posts,
    "note": "Robust investment-focused social sentiment with graceful API failure handling"
}

with open(f"output/social_media_{symbol}.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=4)

print(f"✅ social_media_{symbol}.json generated with {len(posts)} posts")

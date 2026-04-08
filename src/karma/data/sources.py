"""
Data Sources - Every external data fetcher in one place.

All functions return a Python dict (or None on failure).
No CLI, no subprocess, no file I/O. Pure fetch-and-return.

Sources integrated:
  - yfinance      : stock data, fundamentals, balance sheet, income, cashflow
  - Alpha Vantage : news sentiment, company overview
  - Reddit JSON   : social posts from finance subreddits
  - StockTwits    : social sentiment stream
  - Yahoo RSS     : news + social headlines via feedparser
  - Google News   : free news via RSS (no API key needed)

Raw text is returned without pre-computed sentiment scores.
LLM agents are responsible for their own sentiment analysis.

Each source function is named:  <source>_<data_type>
    e.g.  yfinance_stock(), alphavantage_news(), reddit_social()

They all follow the same contract:
    def source_name(ticker: str, **kwargs) -> Optional[Dict]:
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy imports — each source only imported when called
# ---------------------------------------------------------------------------

def _safe_import(module_name: str):
    """Import a module, return None if not installed."""
    try:
        import importlib
        return importlib.import_module(module_name)
    except ImportError:
        logger.warning("Module '%s' not installed — run: pip install %s", module_name, module_name)
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  TEXT FILTERING HELPERS  (noise reduction for social + news)
# ═══════════════════════════════════════════════════════════════════════════

# Investment-relevant keywords for filtering noise
INVESTMENT_KEYWORDS = [
    "stock", "shares", "earnings", "revenue", "profit",
    "loss", "guidance", "valuation", "price target",
    "upgrade", "downgrade", "buy", "sell", "hold",
    "bullish", "bearish", "institutional",
    "results", "forecast", "outperform", "underperform",
    "analyst", "rating", "quarter", "fiscal",
    "dividend", "acquisition", "merger", "buyback",
]

EXCLUDE_KEYWORDS = [
    "conference", "summit", "agenda", "appoints",
    "names chief", "unveils", "funding", "series a",
    "event", "expo", "webinar", "hiring",
    "etf", "gold", "crypto", "bitcoin",
]

FINANCE_SUBREDDITS = {
    "stocks", "investing", "stockmarket", "options",
    "securityanalysis", "valueinvesting", "wallstreetbets",
}


def _is_investment_text(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in INVESTMENT_KEYWORDS)


# ═══════════════════════════════════════════════════════════════════════════
#  YFINANCE SOURCES
# ═══════════════════════════════════════════════════════════════════════════

def yfinance_stock(ticker: str, date: str = None, days: int = 30) -> Optional[Dict]:
    """
    Fetch stock price history from yfinance.

    Returns dict with keys: ticker, period, prices (list of OHLCV dicts),
    summary stats (change %, volatility, trend).
    """
    yf = _safe_import("yfinance")
    np = _safe_import("numpy")
    if yf is None:
        return None

    try:
        stock = yf.Ticker(ticker)

        if date:
            end = datetime.strptime(date, "%Y-%m-%d")
        else:
            end = datetime.now()
        start = end - timedelta(days=days)

        hist = stock.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))
        if hist.empty:
            return None

        prices = []
        for idx, row in hist.iterrows():
            prices.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })

        # Summary stats
        closes = hist["Close"]
        price_start = float(closes.iloc[0])
        price_end = float(closes.iloc[-1])
        change_pct = round(((price_end - price_start) / price_start) * 100, 2)

        volatility = None
        if np:
            daily_ret = closes.pct_change().dropna()
            volatility = round(float(np.std(daily_ret) * np.sqrt(252)), 4)

        return {
            "ticker": ticker,
            "period": f"{days}d ending {end.strftime('%Y-%m-%d')}",
            "data_source": "yfinance",
            "price_count": len(prices),
            "summary": {
                "start_price": price_start,
                "end_price": price_end,
                "change_pct": change_pct,
                "trend": "bullish" if change_pct > 0 else "bearish",
                "annualized_volatility": volatility,
            },
            "prices": prices,
        }
    except Exception as e:
        logger.warning("yfinance_stock failed for %s: %s", ticker, e)
        return None


def yfinance_fundamentals(ticker: str) -> Optional[Dict]:
    """
    Fetch fundamentals from yfinance (valuation, profitability, health, growth).
    """
    yf = _safe_import("yfinance")
    if yf is None:
        return None

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or "symbol" not in info:
            return None

        return {
            "company": info.get("longName", ticker),
            "ticker": ticker,
            "data_source": "yfinance",
            "as_of": datetime.now().strftime("%Y-%m-%d"),
            "fundamentals": {
                "valuation": {
                    "market_cap": info.get("marketCap"),
                    "pe_ratio": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "peg_ratio": info.get("pegRatio"),
                    "price_to_book": info.get("priceToBook"),
                    "valuation_signal": (
                        "fair" if (info.get("trailingPE") or 999) < 35 else "expensive"
                    ),
                },
                "profitability": {
                    "eps": info.get("trailingEps"),
                    "operating_margin": info.get("operatingMargins"),
                    "net_margin": info.get("profitMargins"),
                    "roe": info.get("returnOnEquity"),
                    "profitability_signal": (
                        "strong" if (info.get("profitMargins") or 0) > 0.2 else "weak"
                    ),
                },
                "financial_health": {
                    "free_cash_flow": info.get("freeCashflow"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "cash_on_hand": info.get("totalCash"),
                    "current_ratio": info.get("currentRatio"),
                    "health_signal": (
                        "very strong" if (info.get("debtToEquity") or 999) < 50 else "moderate"
                    ),
                },
                "growth": {
                    "revenue_growth_yoy": info.get("revenueGrowth"),
                    "eps_growth_yoy": info.get("earningsGrowth"),
                    "growth_signal": (
                        "strong" if (info.get("revenueGrowth") or 0) > 0.1 else "moderate"
                    ),
                },
            },
        }
    except Exception as e:
        logger.warning("yfinance_fundamentals failed for %s: %s", ticker, e)
        return None


def yfinance_market_report(ticker: str) -> Optional[Dict]:
    """
    Generate a market context report: stock momentum, sector ETF comparison, VIX risk.
    """
    yf = _safe_import("yfinance")
    np = _safe_import("numpy")
    if yf is None:
        return None

    SECTOR_ETF_MAP = {
        "Information Technology": "XLK",
        "Technology": "XLK",
        "Communication Services": "XLC",
        "Consumer Discretionary": "XLY",
        "Consumer Cyclical": "XLY",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Energy": "XLE",
        "Industrials": "XLI",
    }

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")
        if hist.empty or len(hist) < 2:
            return None

        price_start = float(hist["Close"].iloc[0])
        price_end = float(hist["Close"].iloc[-1])
        change_pct = round(((price_end - price_start) / price_start) * 100, 2)
        trend = "bullish" if change_pct > 0 else "bearish"

        volatility = None
        volatility_signal = "unknown"
        if np:
            daily_ret = hist["Close"].pct_change().dropna()
            volatility = round(float(np.std(daily_ret) * np.sqrt(252)), 4)
            if volatility > 0.35:
                volatility_signal = "high"
            elif volatility > 0.20:
                volatility_signal = "moderate"
            else:
                volatility_signal = "low"

        # Sector comparison
        info = stock.info
        sector = info.get("sector", "Unknown")
        etf_symbol = SECTOR_ETF_MAP.get(sector)
        sector_return = None
        relative = "unknown"

        if etf_symbol:
            try:
                etf_hist = yf.Ticker(etf_symbol).history(period="3mo")
                if not etf_hist.empty and len(etf_hist) >= 2:
                    etf_start = float(etf_hist["Close"].iloc[0])
                    etf_end = float(etf_hist["Close"].iloc[-1])
                    sector_return = round(((etf_end - etf_start) / etf_start) * 100, 2)
                    relative = "outperforming" if change_pct > sector_return else "underperforming"
            except Exception:
                pass

        # VIX risk
        vix_avg = None
        risk_level = "unknown"
        try:
            vix_hist = yf.Ticker("^VIX").history(period="3mo")
            if not vix_hist.empty:
                vix_avg = round(float(vix_hist["Close"].mean()), 2)
                if vix_avg > 25:
                    risk_level = "high"
                elif vix_avg > 18:
                    risk_level = "moderate"
                else:
                    risk_level = "low"
        except Exception:
            pass

        return {
            "company": info.get("longName", ticker),
            "ticker": ticker,
            "data_source": "yfinance",
            "time_window": "last_3_months",
            "stock_performance": {
                "price_change_percent": change_pct,
                "trend": trend,
                "volatility": volatility,
                "volatility_signal": volatility_signal,
            },
            "sector_performance": {
                "sector": sector,
                "sector_etf": etf_symbol,
                "sector_3m_return_percent": sector_return,
                "relative_to_sector": relative,
            },
            "risk_context": {
                "vix_average": vix_avg,
                "risk_level": risk_level,
            },
        }
    except Exception as e:
        logger.warning("yfinance_market_report failed for %s: %s", ticker, e)
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  ALPHA VANTAGE SOURCES
# ═══════════════════════════════════════════════════════════════════════════

def _get_av_key() -> Optional[str]:
    """Get Alpha Vantage API key from env or config."""
    key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not key:
        try:
            from karma.config import CONFIG
            key = CONFIG.get("alpha_vantage_api_key")
        except Exception:
            pass
    return key


def alphavantage_news(ticker: str, months: int = 3) -> Optional[Dict]:
    """
    Fetch investment news from Alpha Vantage NEWS_SENTIMENT endpoint.
    Filters to investment-relevant articles, applies sentiment scoring.
    """
    requests = _safe_import("requests")
    if requests is None:
        return None

    api_key = _get_av_key()
    if not api_key:
        logger.warning("No ALPHA_VANTAGE_API_KEY set — skipping AV news")
        return None

    try:
        cutoff = datetime.utcnow() - timedelta(days=months * 30)
        company_terms = [ticker.lower()]

        resp = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "NEWS_SENTIMENT", "tickers": ticker, "apikey": api_key},
            timeout=15,
        )
        data = resp.json()
        feed = data.get("feed", [])

        if not feed:
            return None

        articles = []
        for item in feed:
            try:
                published = datetime.strptime(item["time_published"], "%Y%m%dT%H%M%S")
            except Exception:
                continue

            if published < cutoff:
                continue

            text = (item.get("title", "") + " " + item.get("summary", "")).lower()
            if not any(k in text for k in INVESTMENT_KEYWORDS):
                continue
            if any(k in text for k in EXCLUDE_KEYWORDS):
                continue

            article = {
                "source": "Alpha Vantage",
                "headline": item.get("title"),
                "summary": item.get("summary"),
                "date": item.get("time_published"),
            }
            # Keep AV's own sentiment if provided (it's API-derived, not ours)
            av_sentiment = item.get("overall_sentiment_label")
            if av_sentiment:
                article["av_sentiment"] = av_sentiment
            articles.append(article)

        if not articles:
            return None

        return {
            "ticker": ticker,
            "data_source": "alpha_vantage",
            "time_window": f"last_{months}_months",
            "article_count": len(articles),
            "articles": articles,
        }
    except Exception as e:
        logger.warning("alphavantage_news failed for %s: %s", ticker, e)
        return None


def alphavantage_fundamentals(ticker: str) -> Optional[Dict]:
    """
    Fetch company overview from Alpha Vantage OVERVIEW endpoint.
    """
    requests = _safe_import("requests")
    if requests is None:
        return None

    api_key = _get_av_key()
    if not api_key:
        return None

    try:
        resp = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "OVERVIEW", "symbol": ticker, "apikey": api_key},
            timeout=15,
        )
        data = resp.json()
        if "Symbol" not in data:
            return None

        return {
            "ticker": ticker,
            "data_source": "alpha_vantage",
            "as_of": data.get("LatestQuarter"),
            "overview": {
                "name": data.get("Name"),
                "sector": data.get("Sector"),
                "industry": data.get("Industry"),
                "market_cap": data.get("MarketCapitalization"),
                "pe_ratio": data.get("PERatio"),
                "peg_ratio": data.get("PEGRatio"),
                "book_value": data.get("BookValue"),
                "eps": data.get("EPS"),
                "dividend_yield": data.get("DividendYield"),
                "profit_margin": data.get("ProfitMargin"),
                "revenue_growth_ttm": data.get("QuarterlyRevenueGrowthYOY"),
            },
        }
    except Exception as e:
        logger.warning("alphavantage_fundamentals failed for %s: %s", ticker, e)
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  SOCIAL MEDIA SOURCES
# ═══════════════════════════════════════════════════════════════════════════

def reddit_social(ticker: str, months: int = 3) -> Optional[Dict]:
    """
    Fetch investment-relevant Reddit posts from finance subreddits.
    Uses Reddit's public JSON API (no auth needed, rate-limited).
    """
    requests = _safe_import("requests")
    if requests is None:
        return None

    try:
        cutoff = datetime.utcnow() - timedelta(days=months * 30)
        headers = {"User-Agent": "Mozilla/5.0 (Investment Research Bot)"}

        url = f"https://www.reddit.com/search.json?q={ticker}&limit=100"
        resp = requests.get(url, headers=headers, timeout=15)

        if resp.status_code != 200 or "application/json" not in resp.headers.get("Content-Type", ""):
            return None

        data = resp.json()
        posts = []

        for item in data.get("data", {}).get("children", []):
            d = item["data"]
            created = datetime.utcfromtimestamp(d.get("created_utc", 0))
            title = d.get("title", "")
            subreddit = d.get("subreddit", "").lower()

            if created < cutoff:
                continue
            if subreddit not in FINANCE_SUBREDDITS:
                continue
            if not _is_investment_text(title):
                continue

            posts.append({
                "platform": "reddit",
                "subreddit": subreddit,
                "text": title,
                "date": created.strftime("%Y-%m-%d"),
            })

        if not posts:
            return None

        return {
            "ticker": ticker,
            "data_source": "reddit",
            "post_count": len(posts),
            "posts": posts,
        }
    except Exception as e:
        logger.warning("reddit_social failed for %s: %s", ticker, e)
        return None


def stocktwits_social(ticker: str) -> Optional[Dict]:
    """
    Fetch sentiment from StockTwits stream.
    """
    requests = _safe_import("requests")
    if requests is None:
        return None

    try:
        cutoff = datetime.utcnow() - timedelta(days=90)
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
        resp = requests.get(url, timeout=10)

        if resp.status_code != 200:
            return None

        data = resp.json()
        posts = []

        for msg in data.get("messages", []):
            try:
                created = datetime.strptime(msg["created_at"][:10], "%Y-%m-%d")
            except Exception:
                continue

            body = msg.get("body", "")
            if created < cutoff:
                continue
            if not _is_investment_text(body):
                continue

            posts.append({
                "platform": "stocktwits",
                "text": body,
                "date": created.strftime("%Y-%m-%d"),
            })

        if not posts:
            return None

        return {
            "ticker": ticker,
            "data_source": "stocktwits",
            "post_count": len(posts),
            "posts": posts,
        }
    except Exception as e:
        logger.warning("stocktwits_social failed for %s: %s", ticker, e)
        return None


def yahoo_social(ticker: str) -> Optional[Dict]:
    """
    Fetch Yahoo Finance RSS headlines as social-like sentiment data.
    """
    fp = _safe_import("feedparser")
    if fp is None:
        return None

    try:
        cutoff = datetime.utcnow() - timedelta(days=90)
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        feed = fp.parse(url)

        posts = []
        for entry in feed.entries:
            if not hasattr(entry, "published_parsed") or not entry.published_parsed:
                continue

            published = datetime(*entry.published_parsed[:6])
            if published < cutoff:
                continue

            text = entry.title + " " + getattr(entry, "summary", "")
            if not _is_investment_text(text):
                continue

            posts.append({
                "platform": "yahoo_finance",
                "text": entry.title,
                "date": published.strftime("%Y-%m-%d"),
            })

        if not posts:
            return None

        return {
            "ticker": ticker,
            "data_source": "yahoo_rss",
            "post_count": len(posts),
            "posts": posts,
        }
    except Exception as e:
        logger.warning("yahoo_social failed for %s: %s", ticker, e)
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  NEWS SOURCES
# ═══════════════════════════════════════════════════════════════════════════

# Ticker → company name for better Google News searches
_TICKER_COMPANY = {
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Google Alphabet",
    "NVDA": "NVIDIA", "AMZN": "Amazon", "TSLA": "Tesla", "META": "Meta",
    "SPY": "S&P 500", "QQQ": "Nasdaq", "AMD": "AMD",
}


def googlenews_rss(ticker: str, days: int = 30) -> Optional[Dict]:
    """
    Fetch news from Google News RSS — free, no API key needed.
    Searches for '{company_name} stock' to get relevant financial news.
    """
    fp = _safe_import("feedparser")
    requests_mod = _safe_import("requests")
    if fp is None:
        return None

    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        company = _TICKER_COMPANY.get(ticker, ticker)
        query = f"{company} {ticker} stock"

        # Google News RSS endpoint — free, no auth
        url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"

        # feedparser can fetch directly, but Google sometimes blocks
        # Try with a proper User-Agent header first
        feed = None
        if requests_mod:
            try:
                resp = requests_mod.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/120.0.0.0 Safari/537.36"
                }, timeout=10)
                if resp.status_code == 200:
                    feed = fp.parse(resp.text)
            except Exception:
                pass

        # Fallback: let feedparser fetch directly
        if feed is None or not feed.entries:
            feed = fp.parse(url)

        if not feed.entries:
            logger.warning("Google News RSS returned 0 entries for %s", ticker)
            return None

        articles = []
        for entry in feed.entries:
            # Parse date
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])

            if published and published < cutoff:
                continue

            headline = entry.get("title", "").strip()
            # Google News titles often end with " - Source Name"
            summary = getattr(entry, "summary", "")
            source_name = ""
            if " - " in headline:
                parts = headline.rsplit(" - ", 1)
                headline = parts[0].strip()
                source_name = parts[1].strip() if len(parts) > 1 else ""

            articles.append({
                "source": source_name or "Google News",
                "headline": headline,
                "summary": summary,
                "date": published.strftime("%Y-%m-%dT%H:%M:%S") if published else "",
                "link": entry.get("link", ""),
            })

        if not articles:
            return None

        return {
            "ticker": ticker,
            "data_source": "google_rss",
            "time_window": f"last_{days}_days",
            "article_count": len(articles),
            "articles": articles,
        }
    except Exception as e:
        logger.warning("googlenews_rss failed for %s: %s", ticker, e)
        return None


def yahoo_news(ticker: str) -> Optional[Dict]:
    """
    Fetch news from Yahoo Finance RSS.
    """
    fp = _safe_import("feedparser")
    if fp is None:
        return None

    try:
        cutoff = datetime.utcnow() - timedelta(days=90)
        company_terms = [ticker.lower()]
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        feed = fp.parse(url)

        articles = []
        for entry in feed.entries:
            if not hasattr(entry, "published_parsed") or not entry.published_parsed:
                continue

            published = datetime(*entry.published_parsed[:6])
            if published < cutoff:
                continue

            text = (entry.title + " " + getattr(entry, "summary", "")).lower()
            if not any(k in text for k in INVESTMENT_KEYWORDS):
                continue
            if any(k in text for k in EXCLUDE_KEYWORDS):
                continue

            articles.append({
                "source": "Yahoo Finance",
                "headline": entry.title,
                "summary": getattr(entry, "summary", ""),
                "date": published.strftime("%Y-%m-%dT%H:%M:%S"),
            })

        if not articles:
            return None

        return {
            "ticker": ticker,
            "data_source": "yahoo_rss",
            "article_count": len(articles),
            "articles": articles,
        }
    except Exception as e:
        logger.warning("yahoo_news failed for %s: %s", ticker, e)
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  REGISTRY — maps (data_type, source_name) → function
# ═══════════════════════════════════════════════════════════════════════════

SOURCE_REGISTRY = {
    # Stock / market data
    ("market", "yfinance"):             yfinance_stock,
    ("market", "yfinance_report"):      yfinance_market_report,
    ("technical", "yfinance"):          yfinance_stock,

    # Fundamentals
    ("fundamentals", "yfinance"):       yfinance_fundamentals,
    ("fundamentals", "alpha_vantage"):  alphavantage_fundamentals,

    # News
    ("news", "google_rss"):            googlenews_rss,
    ("news", "alpha_vantage"):          alphavantage_news,
    ("news", "yahoo_rss"):             yahoo_news,

    # Social media
    ("social", "reddit"):              reddit_social,
    ("social", "stocktwits"):          stocktwits_social,
    ("social", "yahoo_rss"):           yahoo_social,
}


def list_sources(data_type: str = None) -> list:
    """List available source names, optionally filtered by data_type."""
    if data_type:
        return [src for (dt, src) in SOURCE_REGISTRY if dt == data_type]
    return list(set(src for (_, src) in SOURCE_REGISTRY))


def fetch(data_type: str, source_name: str, ticker: str, **kwargs) -> Optional[Dict]:
    """
    Generic fetch: look up (data_type, source_name) in registry and call it.

    >>> fetch("market", "yfinance", "AAPL", date="2024-01-15")
    """
    fn = SOURCE_REGISTRY.get((data_type, source_name))
    if fn is None:
        logger.warning("No source registered for (%s, %s)", data_type, source_name)
        return None
    return fn(ticker, **kwargs)

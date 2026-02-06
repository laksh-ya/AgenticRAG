"""
Data Loader - Unified data loading with fallback chains and file-based caching.

Architecture:
    1. Check JSON cache (data/<subdir>/<TICKER>.json) — instant, no network
    2. Walk the FALLBACK_CHAINS for the data_type, trying each source in order
    3. First source that returns data wins → auto-cache to JSON for next time
    4. If ALL sources fail → return a descriptive "no data" message

Cache behaviour:
    - fundamentals:  cache for 7 days  (doesn't change often)
    - market/tech:   cache for 1 day   (prices change daily)
    - news:          cache for 6 hours (need freshness)
    - social:        cache for 6 hours

Force-refresh:  DataLoader.load(ticker, date, data_type, force_refresh=True)

This is the ONLY module that agents, graphs, and Streamlit apps import for data.
"""
import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#  Lazy import of sources (avoids circular + import cost if not used)
# ---------------------------------------------------------------------------
_sources = None

def _get_sources():
    global _sources
    if _sources is None:
        from dataflows import sources
        _sources = sources
    return _sources


# ═══════════════════════════════════════════════════════════════════════════
#  FALLBACK CHAINS — per data_type, tried in order. Configurable.
# ═══════════════════════════════════════════════════════════════════════════

# Default fallback chains — can be overridden via preferences.CONFIG
DEFAULT_FALLBACK_CHAINS = {
    "fundamentals": ["yfinance", "alpha_vantage"],
    "market":       ["yfinance", "yfinance_report"],
    "technical":    ["yfinance"],
    "news":         ["alpha_vantage", "yahoo_rss"],
    "social":       ["reddit", "stocktwits", "yahoo_rss"],
}

# Cache TTLs in seconds — how long before a cached JSON is considered stale
DEFAULT_CACHE_TTL = {
    "fundamentals": 7 * 24 * 3600,   # 7 days
    "market":       24 * 3600,        # 1 day
    "technical":    24 * 3600,        # 1 day
    "news":         6 * 3600,         # 6 hours
    "social":       6 * 3600,         # 6 hours
}

# Map data_type → subdirectory under data/
DIR_MAP = {
    "fundamentals": "fundamentals",
    "market":       "stock_data",
    "news":         "news",
    "social":       "social_media",
    "technical":    "stock_data",
}


# ═══════════════════════════════════════════════════════════════════════════
#  DataLoader
# ═══════════════════════════════════════════════════════════════════════════

class DataLoader:
    """
    Unified data loader. Used by every agent and Streamlit app.

    API is intentionally simple:
        loader = DataLoader()
        text = loader.load("AAPL", "2024-01-15", "fundamentals")

    That's it. It handles caching, fallback chains, everything.
    """

    def __init__(
        self,
        data_dir: str = None,
        fallback_chains: Dict[str, List[str]] = None,
        cache_ttl: Dict[str, int] = None,
    ):
        # Import config lazily to avoid circular imports
        try:
            from preferences import CONFIG
            cfg = CONFIG
        except ImportError:
            cfg = {}

        self.data_dir = data_dir or cfg.get("data_dir", "./data")
        self.fallback_chains = fallback_chains or cfg.get(
            "fallback_chains", DEFAULT_FALLBACK_CHAINS
        )
        self.cache_ttl = cache_ttl or cfg.get(
            "cache_ttl", DEFAULT_CACHE_TTL
        )

    # ------------------------------------------------------------------
    #  PUBLIC API
    # ------------------------------------------------------------------

    def load(
        self,
        ticker: str,
        date: str,
        data_type: str,
        force_refresh: bool = False,
    ) -> str:
        """
        Load data as a string (ready to paste into an LLM prompt).

        Tries: JSON cache → fallback sources → error message.
        """
        # 1. Cache check (skip if force_refresh)
        if not force_refresh:
            cached = self._try_cache(ticker, date, data_type)
            if cached is not None:
                logger.debug("Cache hit for %s/%s/%s", ticker, date, data_type)
                return cached

        # 2. Walk fallback chain
        sources = _get_sources()
        chain = self.fallback_chains.get(data_type, [])

        for source_name in chain:
            try:
                # Build kwargs based on data_type
                kwargs = {}
                if data_type in ("market", "technical"):
                    kwargs["date"] = date
                    kwargs["days"] = 30

                result = sources.fetch(data_type, source_name, ticker, **kwargs)
                if result:
                    logger.info(
                        "✅ %s/%s fetched from %s (%d keys)",
                        ticker, data_type, source_name, len(result),
                    )
                    # Auto-cache the result
                    self._save_cache(ticker, data_type, result, date)
                    return json.dumps(result, indent=2, default=str)

            except Exception as e:
                logger.warning(
                    "Source %s failed for %s/%s: %s", source_name, ticker, data_type, e
                )
                continue

        # 3. Nothing worked
        subdir = DIR_MAP.get(data_type, data_type)
        return (
            f"No {data_type} data found for {ticker} on {date}. "
            f"Tried sources: {chain}. "
            f"Place a JSON file at data/{subdir}/{ticker}.json or check API keys."
        )

    def load_dict(
        self,
        ticker: str,
        date: str,
        data_type: str,
        force_refresh: bool = False,
    ) -> Optional[Dict]:
        """
        Like load(), but returns parsed dict (or None) instead of string.
        Useful for Streamlit apps that want to inspect the data structure.
        """
        text = self.load(ticker, date, data_type, force_refresh)
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None

    def fetch_all(
        self,
        ticker: str,
        date: str,
        force_refresh: bool = False,
    ) -> Dict[str, str]:
        """
        Fetch ALL data types for a ticker. Returns dict of {data_type: text}.
        Useful for bulk prefetch or Streamlit testing.
        """
        results = {}
        for data_type in ["fundamentals", "market", "news", "social"]:
            results[data_type] = self.load(ticker, date, data_type, force_refresh)
        return results

    def prefetch(
        self,
        tickers: List[str],
        date: str,
        data_types: List[str] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Dict[str, str]]:
        """
        Bulk prefetch: fetch data for multiple tickers and types.
        Returns {ticker: {data_type: status_message}}.
        """
        data_types = data_types or ["fundamentals", "market", "news", "social"]
        results = {}
        for ticker in tickers:
            results[ticker] = {}
            for dt in data_types:
                text = self.load(ticker, date, dt, force_refresh)
                is_error = text.startswith("No ")
                results[ticker][dt] = "❌ no data" if is_error else f"✅ {len(text)} chars"
        return results

    # ------------------------------------------------------------------
    #  CACHE MANAGEMENT
    # ------------------------------------------------------------------

    def _try_cache(self, ticker: str, date: str, data_type: str) -> Optional[str]:
        """
        Check JSON cache. Returns string if cache is fresh, None otherwise.
        Tries: TICKER_DATE.json first, then TICKER.json
        """
        subdir = DIR_MAP.get(data_type, data_type)
        candidates = [
            os.path.join(self.data_dir, subdir, f"{ticker}_{date}.json"),
            os.path.join(self.data_dir, subdir, f"{ticker}.json"),
        ]

        ttl = self.cache_ttl.get(data_type, 24 * 3600)

        for path in candidates:
            if not os.path.exists(path):
                continue

            # Check freshness
            file_age = time.time() - os.path.getmtime(path)
            if file_age > ttl:
                logger.debug("Cache stale for %s (age=%.0fs, ttl=%ds)", path, file_age, ttl)
                continue

            try:
                with open(path, "r") as f:
                    data = json.load(f)
                return json.dumps(data, indent=2)
            except Exception as e:
                logger.warning("Cache read error for %s: %s", path, e)

        return None

    def _save_cache(self, ticker: str, data_type: str, data: dict, date: str = None):
        """Save fetched data to JSON cache."""
        subdir = DIR_MAP.get(data_type, data_type)
        dir_path = os.path.join(self.data_dir, subdir)
        os.makedirs(dir_path, exist_ok=True)

        # Use date-specific filename for time-sensitive data, plain for fundamentals
        if data_type == "fundamentals":
            filename = f"{ticker}.json"
        else:
            filename = f"{ticker}_{date}.json" if date else f"{ticker}.json"

        path = os.path.join(dir_path, filename)
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug("Cached %s → %s", data_type, path)
        except Exception as e:
            logger.warning("Cache write error: %s", e)

    def cache_status(self, ticker: str = None) -> Dict[str, Any]:
        """
        Get cache status for all data types (or a specific ticker).
        Returns info about what's cached, how old, and freshness.
        """
        status = {}
        for data_type, subdir in DIR_MAP.items():
            if data_type == "technical":
                continue  # same dir as market, skip duplicate

            dir_path = os.path.join(self.data_dir, subdir)
            ttl = self.cache_ttl.get(data_type, 24 * 3600)
            type_status = {"dir": subdir, "ttl_hours": ttl / 3600, "files": []}

            if os.path.exists(dir_path):
                for fname in sorted(os.listdir(dir_path)):
                    if not fname.endswith(".json"):
                        continue
                    if ticker and not fname.startswith(ticker):
                        continue

                    path = os.path.join(dir_path, fname)
                    age = time.time() - os.path.getmtime(path)
                    size = os.path.getsize(path)
                    type_status["files"].append({
                        "file": fname,
                        "age_hours": round(age / 3600, 1),
                        "size_kb": round(size / 1024, 1),
                        "fresh": age <= ttl,
                    })

            status[data_type] = type_status

        return status

    def clear_cache(self, data_type: str = None, ticker: str = None):
        """
        Clear cached JSON files.
        - No args: clear everything
        - data_type only: clear that type for all tickers
        - ticker only: clear all types for that ticker
        - both: clear specific
        """
        removed = []
        dirs_to_check = {}

        if data_type:
            subdir = DIR_MAP.get(data_type)
            if subdir:
                dirs_to_check[data_type] = subdir
        else:
            dirs_to_check = {k: v for k, v in DIR_MAP.items() if k != "technical"}

        for dt, subdir in dirs_to_check.items():
            dir_path = os.path.join(self.data_dir, subdir)
            if not os.path.exists(dir_path):
                continue
            for fname in os.listdir(dir_path):
                if not fname.endswith(".json"):
                    continue
                if ticker and not fname.startswith(ticker):
                    continue
                path = os.path.join(dir_path, fname)
                os.remove(path)
                removed.append(f"{subdir}/{fname}")

        return removed

    def list_available(self, data_type: str = None) -> Dict[str, List[str]]:
        """List available cached data files."""
        result = {}
        subdirs = list(set(DIR_MAP.values()))
        if data_type:
            sd = DIR_MAP.get(data_type)
            subdirs = [sd] if sd else []

        for subdir in subdirs:
            path = os.path.join(self.data_dir, subdir)
            if os.path.exists(path):
                files = sorted(f for f in os.listdir(path) if f.endswith(".json"))
                result[subdir] = files

        return result

    # ------------------------------------------------------------------
    #  SAVE (for external scripts / Streamlit uploads)
    # ------------------------------------------------------------------

    def save_json(self, ticker: str, data_type: str, data: dict, date: str = None) -> str:
        """Save data as JSON file. Returns the file path."""
        self._save_cache(ticker, data_type, data, date)
        subdir = DIR_MAP.get(data_type, data_type)
        if data_type == "fundamentals":
            filename = f"{ticker}.json"
        else:
            filename = f"{ticker}_{date}.json" if date else f"{ticker}.json"
        return os.path.join(self.data_dir, subdir, filename)

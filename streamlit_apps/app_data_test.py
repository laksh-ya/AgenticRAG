"""
Data Pipeline Test App — test every source, inspect cache, bulk fetch, force refresh.

Tabs:
  1. Quick Test      — pick ticker + type → load with fallback → see result
  2. Source Explorer  — test individual sources from sources.py directly
  3. Cache Inspector  — see what's cached, age, freshness, clear cache
  4. Bulk Fetch       — prefetch all tickers × all types in one click
  5. Config           — view / edit fallback chains and cache TTLs live
"""
import streamlit as st
import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataflows.data_loader import DataLoader
from dataflows.sources import SOURCE_REGISTRY, list_sources, fetch
from preferences import SUPPORTED_TICKERS, CONFIG, FALLBACK_CHAINS, CACHE_TTL

st.set_page_config(page_title="Data Pipeline Test", page_icon="🔌", layout="wide")
st.title("🔌 Data Pipeline Test")

loader = DataLoader()

# ═══════════════════════════════════════════════════════════════════════════
#  Tabs
# ═══════════════════════════════════════════════════════════════════════════
tab_quick, tab_sources, tab_cache, tab_bulk, tab_config = st.tabs(
    ["⚡ Quick Test", "🔍 Source Explorer", "📦 Cache Inspector", "📥 Bulk Fetch", "⚙️ Config"]
)

# ─────────────────────────────────────────────────────────────────────────
#  Tab 1 — Quick Test (uses DataLoader with full fallback chain)
# ─────────────────────────────────────────────────────────────────────────
with tab_quick:
    st.subheader("Load data through the full fallback pipeline")
    st.caption("JSON cache → source 1 → source 2 → … → error message")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        qt_ticker = st.selectbox("Ticker", SUPPORTED_TICKERS, key="qt_ticker")
    with col2:
        qt_date = st.date_input("Date", datetime.now(), key="qt_date")
    with col3:
        qt_type = st.selectbox("Data Type", ["fundamentals", "market", "news", "social"], key="qt_type")
    with col4:
        qt_force = st.checkbox("Force refresh", key="qt_force")

    if st.button("🚀 Load", key="qt_load"):
        date_str = qt_date.strftime("%Y-%m-%d")
        start = time.time()
        with st.spinner(f"Loading {qt_type} for {qt_ticker}…"):
            data = loader.load(qt_ticker, date_str, qt_type, force_refresh=qt_force)
        elapsed = time.time() - start

        is_error = data.startswith("No ")
        if is_error:
            st.error(data)
        else:
            st.success(f"✅ Loaded in {elapsed:.2f}s — {len(data):,} chars")

            # Try to parse as JSON for pretty display
            try:
                parsed = json.loads(data)
                source = parsed.get("data_source", "json cache")
                st.info(f"**Source:** {source}")

                # Show summary metrics if available
                if "summary" in parsed:
                    st.json(parsed["summary"])
                elif "fundamentals" in parsed:
                    st.json(parsed["fundamentals"].get("valuation", {}))
                elif "article_count" in parsed:
                    st.metric("Articles", parsed["article_count"])
                elif "post_count" in parsed:
                    st.metric("Posts", parsed["post_count"])

                with st.expander("📄 Full JSON", expanded=False):
                    st.json(parsed)
            except json.JSONDecodeError:
                st.code(data[:3000])

    st.markdown("---")
    st.caption(f"Fallback chain for **{qt_type}**: `{FALLBACK_CHAINS.get(qt_type, [])}`")


# ─────────────────────────────────────────────────────────────────────────
#  Tab 2 — Source Explorer (test individual sources directly)
# ─────────────────────────────────────────────────────────────────────────
with tab_sources:
    st.subheader("Test individual data sources")
    st.caption("Bypass cache & fallback — call a specific source function directly")

    data_types = sorted(set(dt for dt, _ in SOURCE_REGISTRY))
    se_type = st.selectbox("Data type", data_types, key="se_type")

    available = list_sources(se_type)
    se_source = st.selectbox("Source", available, key="se_source")
    se_ticker = st.selectbox("Ticker", SUPPORTED_TICKERS, key="se_ticker")

    col_a, col_b = st.columns(2)
    with col_a:
        se_date = st.date_input("Date", datetime.now(), key="se_date")

    if st.button("🔬 Test Source", key="se_test"):
        kwargs = {}
        if se_type in ("market", "technical"):
            kwargs["date"] = se_date.strftime("%Y-%m-%d")
            kwargs["days"] = 30

        start = time.time()
        with st.spinner(f"Calling {se_source}…"):
            result = fetch(se_type, se_source, se_ticker, **kwargs)
        elapsed = time.time() - start

        if result is None:
            st.error(f"❌ Source `{se_source}` returned None for {se_ticker}")
        else:
            st.success(f"✅ Got data in {elapsed:.2f}s — {len(result)} keys")
            st.json(result)

    st.markdown("---")
    st.subheader("📋 Source Registry")
    registry_table = []
    for (dt, src), fn in sorted(SOURCE_REGISTRY.items()):
        registry_table.append({
            "Data Type": dt,
            "Source": src,
            "Function": fn.__name__,
        })
    st.dataframe(registry_table, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────
#  Tab 3 — Cache Inspector
# ─────────────────────────────────────────────────────────────────────────
with tab_cache:
    st.subheader("Cached data files")

    ci_ticker = st.selectbox(
        "Filter by ticker (leave blank for all)",
        ["(all)"] + SUPPORTED_TICKERS,
        key="ci_ticker",
    )
    filter_ticker = None if ci_ticker == "(all)" else ci_ticker

    status = loader.cache_status(filter_ticker)

    for data_type, info in status.items():
        with st.expander(
            f"**{data_type}** — `data/{info['dir']}/` — TTL: {info['ttl_hours']}h — {len(info['files'])} files",
            expanded=True,
        ):
            if not info["files"]:
                st.caption("No cached files")
                continue

            for f in info["files"]:
                fresh_icon = "🟢" if f["fresh"] else "🔴"
                st.markdown(
                    f"{fresh_icon} **{f['file']}** — "
                    f"{f['age_hours']}h old — "
                    f"{f['size_kb']} KB"
                )

    st.markdown("---")
    col_clear1, col_clear2, col_clear3 = st.columns(3)
    with col_clear1:
        clear_type = st.selectbox(
            "Clear data type",
            ["(all)"] + list(set(t for t, _ in SOURCE_REGISTRY)),
            key="clear_type",
        )
    with col_clear2:
        clear_ticker = st.selectbox(
            "Clear ticker",
            ["(all)"] + SUPPORTED_TICKERS,
            key="clear_ticker",
        )
    with col_clear3:
        if st.button("🗑️ Clear Cache", type="secondary"):
            dt = None if clear_type == "(all)" else clear_type
            tk = None if clear_ticker == "(all)" else clear_ticker
            removed = loader.clear_cache(data_type=dt, ticker=tk)
            if removed:
                st.success(f"Removed {len(removed)} files: {removed}")
            else:
                st.info("Nothing to clear")


# ─────────────────────────────────────────────────────────────────────────
#  Tab 4 — Bulk Fetch
# ─────────────────────────────────────────────────────────────────────────
with tab_bulk:
    st.subheader("Prefetch data for all tickers")
    st.caption("Runs loader.load() for every ticker × every data type. Results get auto-cached.")

    bf_date = st.date_input("Date", datetime.now(), key="bf_date")
    bf_force = st.checkbox("Force refresh (ignore cache)", key="bf_force")

    col_tickers = st.multiselect(
        "Tickers (default: all)",
        SUPPORTED_TICKERS,
        default=SUPPORTED_TICKERS,
        key="bf_tickers",
    )
    col_types = st.multiselect(
        "Data types (default: all)",
        ["fundamentals", "market", "news", "social"],
        default=["fundamentals", "market", "news", "social"],
        key="bf_types",
    )

    if st.button("📥 Fetch All", type="primary", key="bf_fetch"):
        date_str = bf_date.strftime("%Y-%m-%d")
        progress = st.progress(0)
        status_area = st.empty()

        total = len(col_tickers) * len(col_types)
        done = 0
        results = {}

        for ticker in col_tickers:
            results[ticker] = {}
            for dt in col_types:
                status_area.markdown(f"Fetching **{dt}** for **{ticker}**…")
                start = time.time()
                data = loader.load(ticker, date_str, dt, force_refresh=bf_force)
                elapsed = time.time() - start

                is_error = data.startswith("No ")
                results[ticker][dt] = {
                    "status": "❌" if is_error else "✅",
                    "chars": len(data),
                    "time": f"{elapsed:.1f}s",
                }
                done += 1
                progress.progress(done / total)

        status_area.empty()
        progress.empty()

        # Build results table
        rows = []
        for ticker, types in results.items():
            row = {"Ticker": ticker}
            for dt, info in types.items():
                row[dt] = f"{info['status']} {info['chars']:,} chars ({info['time']})"
            rows.append(row)

        st.dataframe(rows, use_container_width=True)
        st.success(f"Done! Fetched {total} data points.")


# ─────────────────────────────────────────────────────────────────────────
#  Tab 5 — Config
# ─────────────────────────────────────────────────────────────────────────
with tab_config:
    st.subheader("Data Pipeline Configuration")
    st.caption("From `preferences.py` — these control the fallback order and caching.")

    col_fc, col_ttl = st.columns(2)

    with col_fc:
        st.markdown("### Fallback Chains")
        st.caption("Sources tried in order after cache miss")
        for dt, chain in FALLBACK_CHAINS.items():
            st.markdown(f"**{dt}:** `{'` → `'.join(chain)}`")

    with col_ttl:
        st.markdown("### Cache TTLs")
        st.caption("How long cached JSON stays fresh")
        for dt, seconds in CACHE_TTL.items():
            hours = seconds / 3600
            st.markdown(f"**{dt}:** {hours:.0f} hours")

    st.markdown("---")
    st.markdown("### API Keys Status")
    keys = {
        "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
        "ALPHA_VANTAGE_API_KEY": bool(os.environ.get("ALPHA_VANTAGE_API_KEY") or CONFIG.get("alpha_vantage_api_key")),
    }
    for key, present in keys.items():
        icon = "✅" if present else "❌"
        st.markdown(f"{icon} `{key}`")

    if not keys["ALPHA_VANTAGE_API_KEY"]:
        st.warning(
            "Alpha Vantage key not set. News from `alpha_vantage` source will fail. "
            "Set `ALPHA_VANTAGE_API_KEY` in your `.env` file or in preferences.py CONFIG."
        )

    st.markdown("---")
    st.markdown("### Source Registry (all available sources)")
    source_list = []
    for (dt, src), fn in sorted(SOURCE_REGISTRY.items()):
        in_chain = src in FALLBACK_CHAINS.get(dt, [])
        source_list.append({
            "Data Type": dt,
            "Source": src,
            "In Fallback Chain": "✅" if in_chain else "—",
            "Function": fn.__name__,
        })
    st.dataframe(source_list, use_container_width=True)

    st.markdown("---")
    st.markdown("### LLM / System Config")
    st.json({
        "llm_provider": CONFIG["llm_provider"],
        "deep_model": CONFIG["deep_model"],
        "quick_model": CONFIG["quick_model"],
        "embedding_provider": CONFIG["embedding_provider"],
        "data_dir": CONFIG["data_dir"],
    })

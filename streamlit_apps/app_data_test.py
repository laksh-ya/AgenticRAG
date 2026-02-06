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
#  Pretty renderer — shows data by type (news → articles, social → posts, etc.)
# ═══════════════════════════════════════════════════════════════════════════

def _render_data_pretty(parsed: dict, data_type: str):
    """
    Render fetched data in a human-readable way depending on data_type.
    Shows articles as clickable cards, posts as a table, fundamentals as metrics, etc.
    """
    # ── NEWS: show article cards ──
    if data_type == "news" or "articles" in parsed:
        articles = parsed.get("articles", [])
        st.metric("📰 Articles", len(articles))

        for i, a in enumerate(articles):
            headline = a.get("headline", "No headline")
            source = a.get("source", "")
            date = a.get("date", "")
            summary = a.get("summary", "")
            link = a.get("link", "")
            av_sent = a.get("av_sentiment", "")

            badge = f" · `{av_sent}`" if av_sent else ""
            link_md = f"  [🔗 Open]({link})" if link else ""

            with st.expander(f"**{headline}**  _{source}_{badge}", expanded=False):
                cols = st.columns([3, 1])
                with cols[0]:
                    if summary:
                        st.markdown(summary)
                    else:
                        st.caption("No summary available")
                with cols[1]:
                    if date:
                        st.caption(f"📅 {date[:10]}")
                    if link:
                        st.markdown(f"[🔗 Open article]({link})")

    # ── SOCIAL: show posts table + expandable text ──
    elif data_type == "social" or "posts" in parsed:
        posts = parsed.get("posts", [])
        st.metric("💬 Posts", len(posts))

        # Summary table
        table_rows = []
        for p in posts:
            table_rows.append({
                "Platform": p.get("platform", ""),
                "Subreddit": p.get("subreddit", ""),
                "Date": p.get("date", ""),
                "Text": p.get("text", "")[:120] + ("…" if len(p.get("text", "")) > 120 else ""),
            })
        if table_rows:
            st.dataframe(table_rows, use_container_width=True)

        # Full posts
        with st.expander(f"📝 Full post text ({len(posts)} posts)", expanded=False):
            for i, p in enumerate(posts):
                platform = p.get("platform", "unknown")
                sub = f" r/{p['subreddit']}" if p.get("subreddit") else ""
                st.markdown(f"**{i+1}. [{platform}{sub}]** — {p.get('date', '')}")
                st.text(p.get("text", ""))
                st.markdown("---")

    # ── MARKET: show price summary + chart-ready data ──
    elif data_type == "market" or "summary" in parsed:
        summary = parsed.get("summary", {})
        if summary:
            cols = st.columns(4)
            cols[0].metric("Start Price", f"${summary.get('start_price', 0):.2f}")
            cols[1].metric("End Price", f"${summary.get('end_price', 0):.2f}")
            cols[2].metric("Change", f"{summary.get('change_pct', 0):.2f}%")
            cols[3].metric("Trend", summary.get("trend", "—").upper())

            if summary.get("annualized_volatility"):
                st.caption(f"Annualized Volatility: {summary['annualized_volatility']:.4f}")

        # Price table
        prices = parsed.get("prices", [])
        if prices:
            with st.expander(f"📊 Price data ({len(prices)} days)", expanded=False):
                st.dataframe(prices, use_container_width=True)

        # Market report extras
        if "stock_performance" in parsed:
            st.json(parsed["stock_performance"])
        if "sector_performance" in parsed:
            st.json(parsed["sector_performance"])
        if "risk_context" in parsed:
            st.json(parsed["risk_context"])

    # ── FUNDAMENTALS: show key metrics as cards ──
    elif data_type == "fundamentals" or "fundamentals" in parsed:
        fdata = parsed.get("fundamentals", parsed.get("overview", {}))
        company = parsed.get("company", parsed.get("ticker", ""))
        st.markdown(f"**{company}** — as of {parsed.get('as_of', 'N/A')}")

        if isinstance(fdata, dict):
            for section_name, section_data in fdata.items():
                if isinstance(section_data, dict):
                    with st.expander(f"📊 {section_name.replace('_', ' ').title()}", expanded=True):
                        cols = st.columns(min(len(section_data), 4))
                        for j, (k, v) in enumerate(section_data.items()):
                            with cols[j % len(cols)]:
                                label = k.replace("_", " ").title()
                                if isinstance(v, float):
                                    st.metric(label, f"{v:.4f}")
                                else:
                                    st.metric(label, str(v) if v is not None else "N/A")

    # ── FALLBACK: raw JSON ──
    else:
        st.json(parsed)

    # Always offer raw JSON at the bottom
    with st.expander("🔧 Raw JSON", expanded=False):
        st.json(parsed)


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

            try:
                parsed = json.loads(data)
                source = parsed.get("data_source", "json cache")
                st.info(f"**Source:** {source}")
                _render_data_pretty(parsed, qt_type)
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
            _render_data_pretty(result, se_type)

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
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.markdown(
                        f"{fresh_icon} **{f['file']}** — "
                        f"{f['age_hours']}h old — "
                        f"{f['size_kb']} KB"
                    )
                with col_btn:
                    if st.button("👁️ View", key=f"view_{data_type}_{f['file']}"):
                        st.session_state[f"preview_{data_type}_{f['file']}"] = True

                # Show preview if button was clicked
                if st.session_state.get(f"preview_{data_type}_{f['file']}", False):
                    file_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", info["dir"], f["file"]
                    )
                    try:
                        with open(file_path, "r") as fp:
                            cached_data = json.load(fp)
                        _render_data_pretty(cached_data, data_type)
                        if st.button("🔽 Collapse", key=f"collapse_{data_type}_{f['file']}"):
                            st.session_state[f"preview_{data_type}_{f['file']}"] = False
                            st.rerun()
                    except Exception as e:
                        st.error(f"Could not load file: {e}")

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

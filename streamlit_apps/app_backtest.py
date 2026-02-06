"""
Backtest App - 30-day rolling evaluation
Like test.py but with UI
"""
import streamlit as st
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.backtester import Backtester
from preferences import SUPPORTED_TICKERS

st.set_page_config(page_title="Backtest", page_icon="📊", layout="wide")

st.title("📊 Backtest Evaluation")
st.markdown("*Run 30-day rolling analysis and evaluate performance*")

# Config
col1, col2, col3 = st.columns(3)

with col1:
    ticker = st.selectbox("Ticker", SUPPORTED_TICKERS)

with col2:
    end_date = st.date_input("End Date", datetime.now())

with col3:
    days = st.slider("Days to Backtest", 5, 30, 10)

# Run backtest
if st.button("🚀 Run Backtest", type="primary"):
    progress = st.progress(0)
    status = st.empty()
    
    try:
        backtester = Backtester()
        results = []
        
        for i in range(days):
            date = (end_date - timedelta(days=days - i - 1)).strftime("%Y-%m-%d")
            status.text(f"Analyzing {ticker} for {date}...")
            
            result = backtester.run_single(ticker, date)
            results.append(result)
            
            progress.progress((i + 1) / days)
        
        # Store results
        st.session_state["backtest_results"] = results
        st.session_state["backtest_summary"] = backtester.summarize(results)
        
        status.text("✅ Backtest complete!")
        
    except Exception as e:
        st.error(f"Error: {e}")

# Display results
if "backtest_summary" in st.session_state:
    summary = st.session_state["backtest_summary"]
    results = st.session_state["backtest_results"]
    
    # Summary metrics
    st.header("Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Days", summary["total_days"])
    col2.metric("Buy Signals", summary["buy_count"])
    col3.metric("Sell Signals", summary["sell_count"])
    col4.metric("Hold Signals", summary["hold_count"])
    
    # Results table
    st.header("Daily Results")
    
    for result in results:
        with st.expander(f"{result['date']} - {result['decision']} ({result['confidence']:.0%})"):
            st.text(result.get("reasoning", "No reasoning")[:300])
    
    # Download
    st.download_button(
        "Download Results (JSON)",
        data=str(results),
        file_name=f"backtest_{ticker}.json"
    )

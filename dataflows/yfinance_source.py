"""
YFinance Source - Fallback data source when JSON not available
"""
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
import json


def get_stock_data(ticker: str, date: str, days: int = 30) -> str:
    """Get stock price data from yfinance."""
    try:
        end_date = datetime.strptime(date, "%Y-%m-%d")
        start_date = end_date - timedelta(days=days)
        
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            return f"No data found for {ticker}"
        
        # Format as readable string
        result = f"Stock data for {ticker} ({days} days ending {date}):\n\n"
        result += df.to_string()
        return result
    except Exception as e:
        return f"Error fetching stock data: {e}"


def get_fundamentals(ticker: str) -> str:
    """Get fundamental data from yfinance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract key metrics
        data = {
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "peg_ratio": info.get("pegRatio", "N/A"),
            "price_to_book": info.get("priceToBook", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "profit_margins": info.get("profitMargins", "N/A"),
            "revenue_growth": info.get("revenueGrowth", "N/A"),
            "debt_to_equity": info.get("debtToEquity", "N/A"),
            "current_ratio": info.get("currentRatio", "N/A"),
            "free_cash_flow": info.get("freeCashflow", "N/A"),
        }
        
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error fetching fundamentals: {e}"


def get_balance_sheet(ticker: str) -> str:
    """Get balance sheet from yfinance."""
    try:
        stock = yf.Ticker(ticker)
        bs = stock.balance_sheet
        
        if bs.empty:
            return f"No balance sheet data for {ticker}"
        
        return bs.to_string()
    except Exception as e:
        return f"Error fetching balance sheet: {e}"


def get_income_statement(ticker: str) -> str:
    """Get income statement from yfinance."""
    try:
        stock = yf.Ticker(ticker)
        income = stock.income_stmt
        
        if income.empty:
            return f"No income statement data for {ticker}"
        
        return income.to_string()
    except Exception as e:
        return f"Error fetching income statement: {e}"


def get_cashflow(ticker: str) -> str:
    """Get cash flow from yfinance."""
    try:
        stock = yf.Ticker(ticker)
        cf = stock.cashflow
        
        if cf.empty:
            return f"No cashflow data for {ticker}"
        
        return cf.to_string()
    except Exception as e:
        return f"Error fetching cashflow: {e}"

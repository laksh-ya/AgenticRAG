# AgenticRAG — Multi-Agent Multi-RAG Investment Decision System

A multi-agent system where a **Knowledge Base Agent** actively queries, stores, and **learns from its own trading decisions** via RAG — making it *Agentic RAG*, not passive retrieval.

---

## 🧠 Core Novelty

| What | How |
|------|-----|
| **Pre-Query** | KB Agent searches RAG for past lessons *before* analysts run |
| **Post-Learn** | Every decision is stored with full context in the knowledge base |
| **Outcome Learning** | Feed back real returns → the system reflects and stores lessons |
| **Explainability** | Every decision gets a structured report explaining *why* |

Over time, the system gets smarter because its RAG remembers what worked and what didn't.

---

## 📁 Project Structure

```
AgenticRAG/
├── preferences.py              # Central config — LLMs, embeddings, data, tickers
├── main.py                     # CLI entry point
│
├── agents/                     # All agent logic
│   ├── kb_agent.py             # ★ THE NOVELTY — Knowledge Base Agent
│   ├── analysts.py             # 4 analysts (fundamentals, market, news, social)
│   ├── researchers.py          # Bull + Bear researchers + Research Manager
│   ├── risk_manager.py         # Portfolio-aware risk assessment
│   ├── trader.py               # Final decision maker
│   ├── prompts.py              # All LLM prompts
│   └── state.py                # Shared TypedDict state
│
├── multi_rag/                  # RAG system (ChromaDB)
│   ├── rag_manager.py          # 3 collections: insights, history, lessons
│   ├── knowledge_store.py      # Low-level ChromaDB wrapper
│   ├── embeddings.py           # OpenAI / Gemini / Ollama embeddings
│   └── explainability.py       # 2-phase: snapshot report + outcome learning
│
├── dataflows/                  # ★ Unified data pipeline
│   ├── sources.py              # Every data fetcher (yfinance, Reddit, AV, RSS)
│   ├── data_loader.py          # Cache + fallback chain loader
│   └── yfinance_source.py      # Legacy yfinance helpers
│
├── graphs/
│   └── trading_graph.py        # LangGraph workflow orchestrator
│
├── streamlit_apps/             # 5 Streamlit UIs
│   ├── app_main.py             # Full analysis with live agent reasoning
│   ├── app_data_test.py        # Test all data sources + cache
│   ├── app_kb_train.py         # Teach outcomes, upload data, browse KB
│   ├── app_rag_test.py         # Query RAG directly
│   └── app_backtest.py         # Rolling backtest
│
├── data_ingestion/             # Teammate's standalone scripts (reference)
├── evaluation/                 # Backtesting module
├── paper/                      # Research paper (LaTeX + Markdown)
├── tests/                      # Unit tests
└── utils/                      # LLM factory
```

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone <repo-url> && cd AgenticRAG

# 2. Environment
python -m venv venv && source venv/bin/activate

# 3. Dependencies
pip install -r requirements.txt

# 4. API Keys
cp .env.example .env
# Edit .env → add your OPENAI_API_KEY (required)
# Optional: ALPHA_VANTAGE_API_KEY for news data

# 5. Run
python main.py                              # CLI
streamlit run streamlit_apps/app_main.py    # Web UI
```

---

## 📈 Pipeline Flow

```
KB Pre-Query  →  Fundamentals Analyst  →  Market Analyst  →  News Analyst  →  Social Analyst
                                                                                    ↓
KB Post-Learn  ←  Explainability Report  ←  Trader  ←  Risk Manager  ←  Research Manager
                                                                           ↑
                                                                    Bull ↔ Bear Debate
```

---

## 🔌 Data Pipeline

The `DataLoader` handles everything — agents just call `loader.load(ticker, date, data_type)`.

**How it works:**
1. Check JSON cache (`data/<subdir>/TICKER.json`) — instant, no network
2. Walk the fallback chain for that data type, trying each source in order
3. First source that returns data → auto-cached as JSON for next time

**Fallback chains** (configurable in `preferences.py`):

| Data Type | Source 1 | Source 2 | Source 3 |
|-----------|----------|----------|----------|
| fundamentals | yfinance | alpha_vantage | — |
| market | yfinance (prices) | yfinance (report) | — |
| news | alpha_vantage | yahoo_rss | — |
| social | reddit | stocktwits | yahoo_rss |

**Cache TTLs:** fundamentals=7 days, market=1 day, news/social=6 hours.

---

## ⚙️ Configuration

Everything is in **`preferences.py`** — no hardcoded values anywhere else.

```python
# Switch LLM provider
CONFIG["llm_provider"] = "openai"       # or "gemini" or "ollama"
CONFIG["deep_model"]   = "gpt-4o-mini"  # for research manager + trader
CONFIG["quick_model"]  = "gpt-4o-mini"  # for analysts + risk

# Switch embedding provider
CONFIG["embedding_provider"] = "openai"  # or "gemini" or "ollama"

# Supported tickers
SUPPORTED_TICKERS = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN"]
```

---

## 📊 Streamlit Apps

| App | Command | What it does |
|-----|---------|-------------|
| **Main Analysis** | `streamlit run streamlit_apps/app_main.py` | Full pipeline with live agent progress |
| **Data Test** | `streamlit run streamlit_apps/app_data_test.py` | Test sources, inspect cache, bulk fetch |
| **KB Training** | `streamlit run streamlit_apps/app_kb_train.py` | Teach outcomes, upload data, browse KB |
| **RAG Test** | `streamlit run streamlit_apps/app_rag_test.py` | Query RAG collections directly |
| **Backtest** | `streamlit run streamlit_apps/app_backtest.py` | Rolling 30-day backtest |

---

## 🤝 Contributing

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the full guide on how to edit, where to add things, and what NOT to touch.

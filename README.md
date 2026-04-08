# KARMA — Knowledge-Aware Reinforced Multi-Agent Framework for Autonomous Financial Investment Decision-Making

A multi-agent system where a **Knowledge Base Agent** actively queries, stores, and **learns from its own intraday trading decisions** via RAG — making it *Agentic RAG*, not passive retrieval.

> **Focus:** Intraday trading decisions for US equities. Each analysis generates a BUY/HOLD/SELL recommendation for same-day or next-day action.

---

## 🧠 Core Novelty

| What | How |
|------|-----|
| **Pre-Query** | KB Agent searches RAG for past lessons *before* analysts run |
| **Post-Learn** | Every intraday decision is stored with full context in the knowledge base |
| **Outcome Learning** | Feed back real intraday returns → the system reflects and stores lessons |
| **Explainability** | Every decision gets a structured report explaining *why* |

Over time, the system gets smarter because its RAG remembers what worked and what didn't in intraday trading scenarios.

---

## 📁 Project Structure

```
AgenticRAG/
├── main.py
├── requirements.txt
├── apps/                       # Streamlit apps
│   ├── app_essential.py
│   ├── app_main.py
│   └── app_master_eval.py
├── src/karma/
│   ├── config.py               # Central config (single source of truth)
│   ├── agents/
│   ├── data/
│   ├── rag/
│   ├── graph/
│   ├── evaluation/
│   └── utils/
├── storage/
│   ├── cache/                  # JSON cache
│   ├── kb/                     # Chroma knowledge stores
│   ├── results/                # Analysis + eval outputs
│   └── logs/
├── data/                       # Input dataset snapshots
├── docs/
└── tests/
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
python main.py
streamlit run apps/app_main.py
streamlit run apps/app_essential.py
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
1. Check JSON cache in `storage/cache/<subdir>/...` — instant, no network
2. Walk the fallback chain for that data type, trying each source in order
3. First source that returns data → auto-cached as JSON for next time

**Fallback chains** (configurable in `src/karma/config.py`):

| Data Type | Source 1 | Source 2 | Source 3 |
|-----------|----------|----------|----------|
| fundamentals | yfinance | alpha_vantage | — |
| market | yfinance (prices) | yfinance (report) | — |
| news | google_rss | alpha_vantage | — |
| social | reddit | stocktwits | — |

**Cache TTLs:** fundamentals=7 days, market=1 day, news/social=6 hours.

---

## ⚙️ Configuration

Everything is in **`src/karma/config.py`** — no hardcoded values anywhere else.

```python
# Switch LLM provider
CONFIG["llm_provider"] = "openai"       # or "gemini" or "ollama"
CONFIG["deep_model"]   = "gpt-4o"      # for research manager + trader
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
| **Essential Lab** | `streamlit run apps/app_essential.py` | View decisions, edit cached data/KB, and learn from outcomes |
| **Main Analysis** | `streamlit run apps/app_main.py` | Full pipeline with live agent progress |
| **Master Eval** | `streamlit run apps/app_master_eval.py` | Controlled 5-day KB mode experiment with result tables |

---

## 🤝 Contributing

See **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** for the full guide on how to edit, where to add things, and what NOT to touch.

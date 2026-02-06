# Contributing to AgenticRAG

Rules and reference so all teammates can collaborate without breaking things.

---

## 📋 Table of Contents

1. [Setup](#-setup)
2. [Project Architecture](#-project-architecture)
3. [Where to Edit What](#-where-to-edit-what)
4. [How to Add a New Data Source](#-how-to-add-a-new-data-source)
5. [How to Add / Edit an Agent](#-how-to-add--edit-an-agent)
6. [How to Add a Streamlit App](#-how-to-add-a-streamlit-app)
7. [Configuration Rules](#-configuration-rules)
8. [Git Rules](#-git-rules)
9. [File Ownership Map](#-file-ownership-map)
10. [Common Mistakes](#-common-mistakes)

---

## 🛠 Setup

```bash
# Clone + setup
git clone <repo-url> && cd AgenticRAG
python -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows
pip install -r requirements.txt

# API keys
cp .env.example .env
# Edit .env with your keys (at minimum OPENAI_API_KEY)
```

**Required keys:**
| Key | Required? | Where to get it |
|-----|-----------|----------------|
| `OPENAI_API_KEY` | ✅ Yes | [platform.openai.com](https://platform.openai.com/api-keys) |
| `ALPHA_VANTAGE_API_KEY` | Optional | [alphavantage.co](https://www.alphavantage.co/support/#api-key) (free) |

---

## 🏗 Project Architecture

```
                     preferences.py  ← single source of truth for ALL config
                          │
                          ▼
┌──────────────────────────────────────────────────┐
│                  graphs/trading_graph.py          │  ← orchestrator (LangGraph)
│                                                    │
│   KB Pre-Query → Analysts → Bull/Bear → Risk →    │
│   Trader → Explainability → KB Post-Learn          │
└──────────┬───────────┬────────────┬───────────────┘
           │           │            │
     agents/      dataflows/    multi_rag/
     (LLM calls)  (data fetch)  (ChromaDB)
```

### Key design rules:
- **`preferences.py`** is the ONLY place for config values (models, tickers, TTLs, chains)
- **`dataflows/sources.py`** is the ONLY place for data fetch functions
- **`dataflows/data_loader.py`** is the ONLY module agents use for data (never call sources directly from agents)
- **`agents/state.py`** defines the shared state — all agents read/write to this TypedDict
- **`graphs/trading_graph.py`** wires everything together — DON'T put business logic here

---

## 📍 Where to Edit What

| I want to... | Edit this file |
|--------------|---------------|
| Change LLM model / provider | `preferences.py` → `CONFIG` |
| Add a supported ticker | `preferences.py` → `SUPPORTED_TICKERS` |
| Change fallback order for data | `preferences.py` → `FALLBACK_CHAINS` |
| Change cache duration | `preferences.py` → `CACHE_TTL` |
| Add a new data source (API) | `dataflows/sources.py` (see guide below) |
| Fix how data is loaded/cached | `dataflows/data_loader.py` |
| Change an analyst's prompt | `agents/prompts.py` |
| Change analyst logic | `agents/analysts.py` |
| Change bull/bear debate | `agents/researchers.py` |
| Change risk assessment | `agents/risk_manager.py` |
| Change final trading logic | `agents/trader.py` |
| Change KB learning behavior | `agents/kb_agent.py` |
| Change what's in shared state | `agents/state.py` |
| Change explainability format | `multi_rag/explainability.py` |
| Change RAG storage logic | `multi_rag/rag_manager.py` |
| Change the pipeline order | `graphs/trading_graph.py` |
| Add a new Streamlit page | `streamlit_apps/app_<name>.py` |

---

## 🔌 How to Add a New Data Source

**Example:** Adding Finnhub news.

### Step 1: Write the fetcher in `dataflows/sources.py`

```python
def finnhub_news(ticker: str, months: int = 3) -> Optional[Dict]:
    """Fetch news from Finnhub API."""
    requests = _safe_import("requests")
    if requests is None:
        return None

    api_key = os.environ.get("FINNHUB_API_KEY")
    if not api_key:
        logger.warning("No FINNHUB_API_KEY set")
        return None

    try:
        resp = requests.get(
            "https://finnhub.io/api/v1/company-news",
            params={"symbol": ticker, "from": "2025-11-01", "to": "2026-02-07",
                    "token": api_key},
            timeout=15,
        )
        data = resp.json()
        if not data:
            return None

        articles = [{"headline": a["headline"], "source": "finnhub", ...} for a in data]
        return {"ticker": ticker, "data_source": "finnhub", "articles": articles}
    except Exception as e:
        logger.warning("finnhub_news failed: %s", e)
        return None
```

### Step 2: Register it in `SOURCE_REGISTRY` (same file, bottom)

```python
SOURCE_REGISTRY = {
    ...
    ("news", "finnhub"):  finnhub_news,    # ← add this line
}
```

### Step 3: Add to fallback chain in `preferences.py`

```python
FALLBACK_CHAINS = {
    ...
    "news": ["alpha_vantage", "finnhub", "yahoo_rss"],   # ← added finnhub
}
```

### Step 4: Add API key to `.env.example`

```
# FINNHUB_API_KEY=your_key_here  (free at finnhub.io)
```

### Step 5: Add dependency to `requirements.txt` if needed

That's it. The `DataLoader` will automatically try it in the fallback chain.

---

## 🤖 How to Add / Edit an Agent

### Editing prompts
All prompts live in `agents/prompts.py`. Each is a string template with `{placeholders}`. Edit the text, don't change the placeholder names (unless you also update the `.format()` call in the agent).

### Adding a new analyst type
1. Add the prompt in `agents/prompts.py`:
   ```python
   TECHNICAL_PROMPT = "You are a technical analyst. Data:\n{data}\n..."
   ```
2. Register it in `agents/analysts.py` — the `create_analyst()` function handles everything:
   ```python
   def create_technical_analyst(llm, data_loader):
       return create_analyst(llm, "technical", data_loader)
   ```
3. Add the node in `graphs/trading_graph.py` (follow the pattern of existing analysts)
4. Add `"technical"` to `CONFIG["selected_analysts"]` in `preferences.py`

### Adding a new state field
Edit `agents/state.py` → add the field to `AgentState` TypedDict. Then any agent can read/write it.

---

## 📱 How to Add a Streamlit App

1. Create `streamlit_apps/app_<name>.py`
2. Start with this template:
   ```python
   import streamlit as st
   import sys, os
   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   
   from preferences import SUPPORTED_TICKERS, CONFIG
   # import whatever else you need
   
   st.set_page_config(page_title="My App", page_icon="🔧")
   st.title("My App")
   # ... your UI code
   ```
3. Run with: `streamlit run streamlit_apps/app_<name>.py`

---

## ⚙️ Configuration Rules

### ✅ DO
- Put ALL config values in `preferences.py`
- Use `os.getenv()` for API keys
- Use `CONFIG.get("key", default)` when reading config in other files
- Add new env vars to `.env.example` (with empty value)

### ❌ DON'T
- Hardcode API keys ANYWHERE
- Hardcode model names in agent files (use `preferences.CONFIG`)
- Hardcode ticker lists (use `preferences.SUPPORTED_TICKERS`)
- Hardcode file paths (use `preferences.CONFIG["data_dir"]` etc.)

---

## 🔀 Git Rules

### Branch naming
```
feature/<short-name>     # new feature
fix/<short-name>         # bug fix
data/<short-name>        # data source changes
```

### Commit messages
```
feat: add Finnhub news source
fix: handle empty Reddit response
data: update fundamentals cache TTL to 14 days
refactor: clean up trader prompt
docs: update contributing guide
```

### Before pushing, always:
1. `python -m py_compile <your_file.py>` — check for syntax errors
2. Make sure `.env` is in `.gitignore` (it is, don't remove it)
3. `git diff --staged` — review what you're committing
4. Never commit `venv/`, `__pycache__/`, `.env`, `*.json` data files

### What's in `.gitignore` (don't change these):
| Ignored | Reason |
|---------|--------|
| `.env` | API keys — NEVER commit |
| `venv/` | Virtual environment (500MB+) |
| `__pycache__/` | Python bytecode |
| `TradingAgents/` | Reference repo, not our code |
| `knowledge_base/` (DB files) | Local ChromaDB, rebuilds on run |
| `data/**/*.json` | Cached API data, auto-fetched |
| `data_ingestion/output/` | Ingestion script output |
| `results/`, `logs/` | Runtime output |

---

## 👥 File Ownership Map

So we don't step on each other:

| Module | Owner / Primary Editor | What it does |
|--------|----------------------|-------------|
| `preferences.py` | **Anyone** (careful) | Central config |
| `agents/` | Agent logic team | All LLM-calling agents |
| `agents/prompts.py` | Agent logic team | Prompt engineering |
| `dataflows/sources.py` | Data team | All data source fetchers |
| `dataflows/data_loader.py` | Data team | Cache + fallback pipeline |
| `multi_rag/` | RAG team | Vector store + explainability |
| `graphs/trading_graph.py` | **Careful — affects everyone** | Pipeline orchestration |
| `streamlit_apps/` | UI / anyone | Streamlit pages |
| `data_ingestion/` | Data team (reference scripts) | Standalone CLI tools |
| `paper/` | Paper team | Research paper |

### ⚠️ High-risk files (coordinate before editing):
- **`graphs/trading_graph.py`** — changing node order or state keys breaks everything
- **`agents/state.py`** — adding/removing fields affects all agents
- **`preferences.py`** — changing CONFIG keys can break imports across the codebase
- **`multi_rag/rag_manager.py`** — changing collection names wipes existing KB data

---

## ❌ Common Mistakes

| Mistake | Why it's bad | Do this instead |
|---------|-------------|----------------|
| Hardcoding `"gpt-4o-mini"` in an agent | Breaks when someone switches provider | Use `get_quick_llm()` from `utils/llm_factory.py` |
| Calling `yfinance` directly from an agent | Bypasses cache + fallback chain | Use `data_loader.load(ticker, date, "market")` |
| Adding a print statement for debugging | Shows in Streamlit, clutters output | Use `logger.info()` / `logger.debug()` |
| Editing `.gitignore` to include `data/*.json` | Commits 100s of cached API responses | Data is auto-fetched on first run |
| Importing from `data_ingestion/` directly | Those are standalone CLI scripts | Their logic is already in `dataflows/sources.py` |
| Adding a new pip package without updating `requirements.txt` | Teammate's install breaks | Always `pip freeze | grep <pkg>` and add to requirements |

---

## 🧪 Testing Your Changes

```bash
# 1. Syntax check
python -m py_compile <your_file.py>

# 2. Import check (from project root)
python -c "from <module> import <thing>; print('OK')"

# 3. Run the main app
streamlit run streamlit_apps/app_main.py

# 4. Run the data test app (to verify data sources)
streamlit run streamlit_apps/app_data_test.py

# 5. Unit tests (if you wrote any)
python -m pytest tests/
```

---

## 💡 Quick Reference

```python
# Load data (agents use this)
from dataflows.data_loader import DataLoader
loader = DataLoader()
text = loader.load("AAPL", "2026-02-07", "fundamentals")

# Get LLMs (agents use this)
from utils.llm_factory import get_quick_llm, get_deep_llm
llm = get_quick_llm()

# Access config
from preferences import CONFIG, SUPPORTED_TICKERS, FALLBACK_CHAINS

# RAG operations
from multi_rag.rag_manager import RAGManager
rag = RAGManager()
results = rag.query("market_insights", "AAPL earnings", n=5)
```

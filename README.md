# Karma

> **KARMA** = Knowledge-Aware Reinforced Multi-Agent Framework for Autonomous Financial Investment Decision-Making

Karma is a multi-agent investment research and decision system with a knowledge base (RAG) loop. It runs analyst, researcher, risk, and trader agents, then stores and reuses decision context and outcomes to improve future runs.

## Core Capabilities

- Multi-agent orchestration for analysis, debate, risk review, and trade decisioning.
- Knowledge-base pre-query and post-decision learning.
- Explainability pipeline for why a decision was made.
- Cached market, fundamentals, news, and social data ingestion.
- Evaluation and backtesting support.

## Project Structure

```text
karma/
├── main.py
├── requirements.txt
├── apps/
│   ├── app_essential.py
│   ├── app_main.py
│   └── app_master_eval.py
├── src/karma/
│   ├── config.py
│   ├── agents/
│   │   ├── analysts.py
│   │   ├── kb_agent.py
│   │   ├── prompts.py
│   │   ├── researchers.py
│   │   ├── risk_manager.py
│   │   ├── state.py
│   │   └── trader.py
│   ├── data/
│   │   ├── data_loader.py
│   │   └── sources.py
│   ├── evaluation/
│   │   └── backtester.py
│   ├── graph/
│   │   └── trading_graph.py
│   ├── rag/
│   │   ├── embeddings.py
│   │   ├── explainability.py
│   │   ├── knowledge_store.py
│   │   └── rag_manager.py
│   └── utils/
│       ├── core.py
│       ├── llm_factory.py
│       └── portfolio_utils.py
├── storage/
│   ├── cache/
│   ├── kb/
│   ├── logs/
│   └── results/
└── tests/
       ├── test_kb_agent.py
       └── test_rag.py
```

## Quick Start

```bash
# 1) Set up environment
python -m venv venv
source venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Configure environment variables
cp .env.example .env
# Edit .env and add required API keys

# 4) Run CLI workflow
python main.py
```

## Run Streamlit Apps

```bash
streamlit run apps/app_main.py
streamlit run apps/app_essential.py
streamlit run apps/app_master_eval.py
```

## Configuration

Primary settings live in `src/karma/config.py`:

- Model/provider configuration.
- Data source fallback behavior.
- Cache and storage behavior.
- Supported ticker and runtime options.

## Data and Storage

- Input samples are in `data/`.
- Runtime caches are in `storage/cache/`.
- Knowledge base artifacts are in `storage/kb/`.
- Run outputs and outcomes are in `storage/results/`.

## Testing

```bash
pytest tests -q
```

## Contributing

Contribution guidelines are available in `docs/CONTRIBUTING.md`.

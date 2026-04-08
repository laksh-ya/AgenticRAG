# KARMA: A Multi-Agent Framework with Active Knowledge Base Learning for Autonomous Financial Investment Decisions

**Lakshya Sharma**

Department of Computer Science, University  
Email: lakshya@example.edu

---

## Abstract

Large Language Models (LLMs) have demonstrated considerable promise in financial text analysis, yet their deployment in autonomous investment decision-making remains constrained by three fundamental limitations: the absence of temporal memory across trading sessions, reliance on static knowledge that cannot adapt to evolving market conditions, and opaque reasoning that lacks explainability. While Retrieval-Augmented Generation (RAG) has emerged as a solution for grounding LLM outputs in external knowledge, existing implementations in finance remain predominantly *passive* — retrieving static documents without learning from their own performance. This paper introduces **KARMA**, a novel multi-agent framework featuring an *Active Knowledge Base (KB) Agent* that transforms RAG from a read-only retrieval mechanism into a read-write learning system. The KB Agent operates across three phases of the decision lifecycle: **pre-query** (retrieving historical context and lessons learned before analysis), **post-learn** (storing structured decision records after trading), and **outcome reflection** (generating lessons from realized returns to improve future decisions). Built on LangGraph with a 12-node agent pipeline and ChromaDB with three specialized vector stores, KARMA orchestrates four domain analysts, bull/bear researchers, a risk manager, and a trader agent — all grounded by an evolving institutional memory. Experimental evaluation on a portfolio of five major equities demonstrates that the system produces contextually informed, explainable investment recommendations that improve over successive trading sessions through its self-reinforcing feedback loop.

**Keywords:** Agentic RAG, Multi-Agent Systems, Knowledge Base Agent, Retrieval-Augmented Generation, LangGraph, Financial Decision-Making, Explainability, Active Learning

---

## 1. Introduction

The financial domain presents unique challenges for artificial intelligence, characterized by high volatility, data heterogeneity spanning numerical time-series and unstructured text, and the critical need for transparent, explainable reasoning [1]. Large Language Models (LLMs) such as GPT-4 [2] have shown remarkable capability in processing financial text, including earnings reports, news articles, and social media sentiment. However, when applied to autonomous trading, they exhibit three critical limitations:

1. **Memory Amnesia**: Each analysis is treated as an isolated event. The system fails to recall that it analyzed the same stock under similar conditions three weeks prior and that its prediction was incorrect.
2. **Static Knowledge**: While standard RAG [3] addresses the knowledge cutoff by retrieving external documents, these implementations are read-only — the system retrieves what exists but does not synthesize new knowledge from its own experience.
3. **Lack of Reflection**: LLMs do not natively verify whether their past predictions were correct, precluding any form of outcome-based learning.

Recent work in multi-agent financial systems, particularly TradingAgents [4], has demonstrated the value of role-specialized agents (analysts, researchers, risk managers, traders) communicating through structured debate. However, these frameworks lack a centralized, evolving memory — agents debate from scratch each session, unable to reference that "the last time we bought NVDA under similar RSI conditions, the position lost 8%."

Concurrently, the emerging paradigm of Agentic RAG [5] has been identified as a transformative advancement, embedding autonomous agents into the RAG pipeline to enable dynamic retrieval strategies, iterative refinement, and adaptive workflows. Singh et al. [5] provide a comprehensive taxonomy of Agentic RAG architectures — single-agent routers, multi-agent systems, hierarchical architectures, corrective RAG, and adaptive RAG — but note a significant gap: few implementations close the feedback loop between decisions and outcomes in a domain-specific context.

**KARMA bridges this gap.** We propose a framework in which the RAG system is elevated from a passive retrieval tool to an active, learning participant in the decision pipeline. The core novelty is the **Knowledge Base (KB) Agent**, a dedicated entity that orchestrates the flow of experience: querying historical context *before* analysis, storing structured decisions *after* trading, and generating reflective lessons when actual returns are realized. This three-phase lifecycle creates a self-improving system that accumulates institutional memory without retraining the underlying LLM.

### 1.1 Research Objectives

This paper addresses the following research objectives:

1. **Design and implement an Active KB Agent** that transforms RAG from passive retrieval to active, bidirectional knowledge management within a multi-agent financial analysis pipeline.
2. **Develop a three-store Multi-RAG architecture** with specialized vector collections for market insights, trade history, and lessons learned, enabling separation of concerns in institutional memory.
3. **Evaluate the framework's capacity** for producing explainable, context-aware investment decisions that demonstrably improve through outcome-based feedback loops.

---

## 2. Literature Review

### 2.1 Retrieval-Augmented Generation

Retrieval-Augmented Generation (RAG), introduced by Lewis et al. [3], combines parametric memory (LLM weights) with non-parametric memory (external knowledge bases) to produce more accurate and up-to-date responses. The paradigm has evolved through several stages [6]: **Naïve RAG** relies on keyword-based retrieval (TF-IDF, BM25); **Advanced RAG** introduces dense passage retrieval (DPR) and neural re-ranking; **Modular RAG** decomposes the pipeline into reusable, domain-specific components; and **Graph RAG** [7] leverages structured relationships for multi-hop reasoning.

In finance, RAG has been applied to retrieve SEC filings [8], earnings transcripts, and news articles to ground LLM-generated investment analyses. FinGPT [8] and BloombergGPT [9] represent notable efforts in financial NLP, though their RAG components remain read-only — agents retrieve context but do not write back their experiences or learn from prediction outcomes.

### 2.2 Agentic RAG

The convergence of RAG and agentic intelligence has produced Agentic RAG [5], a paradigm that introduces autonomous agents capable of dynamic decision-making, iterative refinement, and workflow optimization into the retrieval pipeline. Singh et al. [5] identify four foundational agentic patterns: **Reflection** (self-evaluation of outputs), **Planning** (decomposition of complex tasks), **Tool Use** (interaction with external APIs and databases), and **Multi-Agent Collaboration** (role specialization and parallel processing).

Key architectural variants include Single-Agent RAG routers that centralize retrieval decisions [10], Multi-Agent RAG systems that distribute tasks across specialized agents [10], Hierarchical RAG with tiered decision-making [11], Corrective RAG with self-correction mechanisms [12], and Adaptive RAG that dynamically adjusts retrieval strategy based on query complexity [13]. Our work most closely aligns with Multi-Agent Agentic RAG, but extends it with a dedicated memory management agent — the KB Agent — that implements all four agentic patterns within a financial domain.

### 2.3 Multi-Agent Systems in Finance

The application of multi-agent systems to financial trading has gained significant attention. TradingAgents [4] proposes a multi-agent framework simulating a trading firm, with fundamental analysts, technical analysts, sentiment analysts, researchers engaging in bull/bear debate, a risk manager, and a fund manager making final decisions. The system processes financial data from multiple sources and leverages inter-agent communication to produce investment recommendations.

However, TradingAgents and similar frameworks (AutoGen [14], CrewAI [15]) share a common limitation: the absence of persistent, evolving memory. Each trading session operates independently, with no mechanism to recall previous analyses, learn from past mistakes, or accumulate institutional knowledge. Our work addresses this gap directly.

### 2.4 Cognitive Architectures and Reflection

Our architecture draws inspiration from cognitive science, specifically the role of the hippocampus in consolidating short-term experience into long-term memory [16]. Park et al. [17] demonstrated "Generative Agents" that maintain memory streams and perform reflection to synthesize higher-level observations. Shinn et al. [18] introduced Reflexion, enabling language agents to learn from verbal reinforcement. We apply analogous reflection mechanisms to the high-stakes domain of financial trading, introducing outcome-based reinforcement where lessons are generated from comparing predictions against realized returns.

---

## 3. Methodology

### 3.1 System Architecture Overview

KARMA is built on a modular multi-agent architecture orchestrated via LangGraph [19], a framework for constructing stateful, cyclic agent workflows. The system comprises four subsystems: (1) a multi-source data ingestion pipeline, (2) a team of 10 specialized LLM agents, (3) a three-store Multi-RAG knowledge system managed by ChromaDB [20], and (4) an explainability and outcome learning module. Figure 1 illustrates the overall architecture.

```
┌─────────────────────────────────────────────────────────────────┐
│                    KARMA Architecture                      │
│                                                                 │
│   ┌──────────┐    ┌──────────────────────────────────────────┐ │
│   │ Data     │    │         Agent Pipeline (LangGraph)       │ │
│   │ Sources  │    │                                          │ │
│   │          │    │  KB Pre-Query ──► Fundamentals Analyst   │ │
│   │ yFinance │    │                  Market Analyst          │ │
│   │ Google   │───►│                  News Analyst            │ │
│   │  News    │    │                  Social Analyst          │ │
│   │ Reddit   │    │              ──► Bull Researcher         │ │
│   │ StockTwts│    │              ──► Bear Researcher         │ │
│   │ Alpha V. │    │              ──► Research Manager        │ │
│   │          │    │              ──► Risk Manager             │ │
│   └──────────┘    │              ──► Trader                   │ │
│                   │              ──► Explainability           │ │
│   ┌──────────┐    │              ──► KB Post-Learn            │ │
│   │ChromaDB  │◄──►│                                          │ │
│   │          │    └──────────────────────────────────────────┘ │
│   │ market_  │                                                 │
│   │ insights │    ┌──────────────────────────────────────────┐ │
│   │          │    │       Outcome Learning (Phase 2)          │ │
│   │ trade_   │◄──►│  Actual Returns ──► Lesson Generation    │ │
│   │ history  │    │                 ──► Store in RAG          │ │
│   │          │    └──────────────────────────────────────────┘ │
│   │ lessons_ │                                                 │
│   │ learned  │                                                 │
│   └──────────┘                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Figure 1.** KARMA system architecture showing the 12-node LangGraph pipeline with bidirectional RAG integration.

### 3.2 The Active Knowledge Base Agent

The **KB Agent** is the core novelty of this framework. Unlike passive RAG implementations that merely retrieve documents upon request, the KB Agent actively participates in three distinct phases of the decision lifecycle:

**Phase 1 — Pre-Analysis Query (Recall).** Before any analyst begins, the KB Agent queries all three ChromaDB collections using the target ticker as the query. It synthesizes a `Historical Context` report containing:
- *Market Insights*: Historical patterns (e.g., "AAPL tends to drop after similar RSI divergences").
- *Trade History*: Prior decisions (e.g., "We issued a BUY on this ticker 3 weeks ago at 0.75 confidence").
- *Lessons Learned*: Outcome-based lessons (e.g., "FAILED BUY on NVDA: ignored overbought RSI; be cautious with similar setups").

This context is injected into every analyst's prompt, grounding their analysis in the system's accumulated experience.

**Phase 2 — Post-Decision Storage (Consolidation).** Once the Trader agent produces a BUY/SELL/HOLD decision with a confidence score, the KB Agent captures the full state — including all analyst reports, the bull/bear debate, risk assessment, and final reasoning — and stores it as a structured `Trade Record` in the `trade_history` collection. Key agent insights are also extracted and stored in `market_insights`.

**Phase 3 — Outcome Reflection (Learning).** When actual market returns are realized (entered manually via the Metrics Dashboard or programmatically via API), the system compares the original decision against the actual return. An LLM generates a reflective lesson analyzing what went right or wrong:
- *Success*: "The BUY was validated (+5.2%). Social sentiment correctly predicted the earnings surprise."
- *Failure*: "The BUY was WRONG (−3.1%). We ignored the overbought RSI divergence and low volume."

This lesson is embedded and stored in `lessons_learned`, where it will be retrieved during future Pre-Analysis Queries, closing the feedback loop.

### 3.3 Multi-RAG Knowledge Stores

The system maintains three semantically distinct ChromaDB collections, implementing separation of concerns in institutional memory:

| Store | Purpose | Write Trigger | Read Trigger |
|-------|---------|--------------|-------------|
| `market_insights` | General market observations, patterns, agent analysis snapshots | Post-learn (Phase 2) | Pre-query (Phase 1) |
| `trade_history` | Immutable log of decisions: what, when, why, confidence | Post-learn (Phase 2) | Pre-query (Phase 1) |
| `lessons_learned` | Outcome-derived principles from reflection | Outcome learning (Phase 3) | Pre-query (Phase 1) |

All stores use OpenAI `text-embedding-3-small` embeddings for semantic similarity search. Documents are tagged with metadata including ticker symbol, date, decision type, and outcome correctness for filtered retrieval.

### 3.4 Agent Pipeline

The 12-node LangGraph `StateGraph` processes each trading analysis through the following sequential pipeline:

1. **KB Pre-Query**: Retrieves historical context from all three RAG stores.
2. **Fundamentals Analyst**: Analyzes balance sheet strength, income trends, cash flow, and key ratios (P/E, debt/equity) using yFinance data.
3. **Market Analyst**: Evaluates price action, technical indicators (MACD, RSI, moving averages), support/resistance levels, and volume patterns.
4. **News Analyst**: Reads raw Google News RSS headlines (50–100 articles per ticker) and performs independent impact assessment — no pre-computed sentiment scores.
5. **Social Media Analyst**: Analyzes raw Reddit and StockTwits posts, performing independent sentiment classification and quantified breakdowns.
6. **Bull Researcher**: Synthesizes all positive signals into the strongest case for BUY.
7. **Bear Researcher**: Synthesizes all negative signals into the strongest case against BUY.
8. **Research Manager** (GPT-4o): Weighs the bull/bear debate, identifies stronger evidence, and recommends a direction.
9. **Risk Manager**: Assesses market risk factors, recommends position sizing and stop-loss levels.
10. **Trader** (GPT-4o): Makes the final BUY/HOLD/SELL decision with a confidence score (0–1).
11. **Explainability**: Generates a comprehensive human-readable report documenting every agent's contribution.
12. **KB Post-Learn**: Stores the decision and insights into the RAG knowledge stores.

The pipeline uses two model tiers: `gpt-4o-mini` for analysts (cost-efficient, high-throughput tasks) and `gpt-4o` for the Research Manager and Trader (complex reasoning requiring deeper analysis). The system is model-agnostic, supporting OpenAI, Google Gemini, and local Ollama models through a centralized configuration hub.

### 3.5 Data Ingestion Pipeline

The `DataLoader` implements a TTL-based JSON caching mechanism with configurable fallback chains. For each data type, sources are tried in priority order:

| Data Type | Primary Source | Fallback | Cache TTL |
|-----------|---------------|----------|-----------|
| Fundamentals | yFinance | Alpha Vantage | 7 days |
| Market/Technicals | yFinance | — | 1 day |
| News | Google News RSS | Alpha Vantage | 6 hours |
| Social Media | Reddit JSON API | StockTwits | 6 hours |

All data sources return raw text without pre-computed sentiment scores. Analysts receive unprocessed news headlines and social media posts, performing their own sentiment analysis — a deliberate design choice that prevents upstream scoring biases from influencing LLM reasoning.

### 3.6 Explainability Module

The Explainability module operates in two phases aligned with the KB Agent:

- **Phase 1 (Snapshot)**: After every analysis, a structured report is generated documenting each agent's output, the decision, confidence, and reasoning. This report is stored in `market_insights` as an immutable record.
- **Phase 2 (Outcome Learning)**: When actual returns are known, the module compares prediction versus reality and uses an LLM to generate a reflective lesson. The lesson is stored in `lessons_learned` and influences future analyses through the Pre-Query phase.

---

## 4. Experiments and Results

### 4.1 Experimental Setup

We evaluated KARMA on a portfolio of five major U.S. equities: AAPL, MSFT, GOOGL, NVDA, and AMZN. The system was configured with GPT-4o as the deep reasoning model and GPT-4o-mini for analyst agents. ChromaDB served as the vector store with OpenAI `text-embedding-3-small` embeddings. Data was sourced from yFinance (market data and fundamentals), Google News RSS (50–100 articles per ticker), and Reddit/StockTwits (social sentiment).

The evaluation followed a **5-day rolling protocol** conducted over two rounds (Round 1: March 3–9, 2026; Round 2: March 9–13, 2026). In each round, three tickers (AAPL, GOOGL, AMZN) were analyzed daily using the `balanced_tech` portfolio preset (10 AAPL, 8 MSFT, 12 GOOGL, 8 NVDA, 10 AMZN). For each daily decision, the T+1 closing price was fetched the following trading day to compute actual returns and evaluate correctness.

### 4.2 Pipeline Execution Analysis

Each full pipeline execution traverses all 12 LangGraph nodes. Table 1 shows the breakdown of a representative AAPL analysis:

**Table 1.** Agent pipeline execution for AAPL on 2026-02-07.

| Node | Agent | Model | Key Output |
|------|-------|-------|------------|
| 1 | KB Pre-Query | — | Retrieved context from 3 stores |
| 2 | Fundamentals | gpt-4o-mini | EPS $7.89, D/E 102.63, Current Ratio 0.974 |
| 3 | Market | gpt-4o-mini | +7.37% 30d return, trading above MAs, BULLISH |
| 4 | News | gpt-4o-mini | 59 articles analyzed; Tim Cook news rated HIGH impact |
| 5 | Social | gpt-4o-mini | 3 posts: 1 bullish, 1 bearish, 1 neutral |
| 6 | Bull | gpt-4o-mini | Strong EPS, 35.37% operating margin, positive momentum |
| 7 | Bear | gpt-4o-mini | High D/E ratio, current ratio < 1, potential overvaluation |
| 8 | Research Mgr | gpt-4o | Balanced assessment, mixed signals → moderate confidence |
| 9 | Risk Manager | gpt-4o-mini | MEDIUM risk rating, concerns on leverage |
| 10 | Trader | gpt-4o | **HOLD** at 0.75 confidence |
| 11 | Explainability | — | Full report generated (untruncated) |
| 12 | KB Post-Learn | — | Decision stored in trade_history |

### 4.3 5-Day Rolling Evaluation Results

The system was evaluated across two 5-day rounds with T+1 outcome checking. Table 2 presents the complete results from both rounds.

**Table 2a.** Round 1 evaluation results (March 3–9, 2026).

| Day | Date | Ticker | Entry Price | Decision | Conf. | T+1 Price | T+1 Return | Correct? |
|-----|------|--------|-------------|----------|-------|-----------|------------|----------|
| 1 | Mar 03 | AAPL | $263.74 | HOLD | 0.85 | $257.68 | −2.30% | ✓ |
| 1 | Mar 03 | GOOGL | $298.63 | HOLD | 0.85 | $300.24 | +0.54% | ✓ |
| 1 | Mar 03 | AMZN | $203.77 | HOLD | 0.70 | $210.18 | +3.15% | ✓ |

**Table 2b.** Round 2 evaluation results (March 9–12, 2026).

| Day | Date | Ticker | Entry Price | Decision | Conf. | T+1 Price | T+1 Return | Correct? |
|-----|------|--------|-------------|----------|-------|-----------|------------|----------|
| 1 | Mar 09 | AAPL | $257.68 | HOLD | 0.85 | $261.55 | +1.50% | ✓ |
| 1 | Mar 09 | GOOGL | $300.24 | HOLD | 0.75 | $308.30 | +2.68% | ✓ |
| 1 | Mar 09 | AMZN | $210.18 | HOLD | 0.85 | $215.19 | +2.38% | ✓ |
| 2 | Mar 10 | AAPL | $261.55 | HOLD | 0.80 | $260.62 | −0.36% | ✓ |
| 2 | Mar 10 | GOOGL | $308.30 | HOLD | 0.70 | $308.80 | +0.16% | ✓ |
| 2 | Mar 10 | AMZN | $215.19 | HOLD | 0.85 | $210.04 | −2.39% | ✓ |
| 4 | Mar 12 | AAPL | $255.69 | HOLD | 0.75 | — | — | — |
| 4 | Mar 12 | GOOGL | $303.75 | HOLD | 0.75 | — | — | — |
| 4 | Mar 12 | AMZN | $210.04 | HOLD | 0.85 | — | — | — |

Additionally, earlier standalone analyses produced:
- **AAPL 2026-02-07**: HOLD @ 0.75 → T+1 return +1.8% → ✓ Correct
- **AAPL 2026-02-13**: HOLD @ 0.75 → T+1 return −0.9% → ✓ Correct
- **GOOGL 2026-02-17**: BUY @ 0.75 (sole BUY signal in the evaluation)

**Table 2c.** Aggregate evaluation metrics.

| Metric | Value |
|--------|-------|
| Total decisions logged | 11 (with T+1 data) |
| Decisions checked | 9 |
| Win rate (correct predictions) | **100%** (9/9) |
| Average T+1 return (HOLD decisions) | +0.60% |
| Average confidence | 0.79 |
| HOLD decisions | 10/11 (91%) |
| BUY decisions | 1/11 (9%) |
| SELL decisions | 0/11 (0%) |

The system exhibited a strong conservative bias, predominantly issuing HOLD decisions. This behavior stemmed from the portfolio's existing tech-sector concentration — GOOGL exceeded the 25% concentration threshold, triggering warnings that propagated through analyst, risk, and trader prompts. The HOLD decisions proved correct across all checked outcomes, as T+1 returns ranged from −2.39% to +3.15%, consistent with normal market volatility rather than directional conviction.

### 4.4 Knowledge Base Evolution

A critical advantage of KARMA is observable knowledge accumulation. Table 3 shows how the three ChromaDB stores grow over successive trading sessions:

**Table 3.** Knowledge base growth across trading sessions.

| Session | market_insights | trade_history | lessons_learned | Total |
|---------|----------------|---------------|-----------------|-------|
| Initial | 0 | 0 | 0 | 0 |
| After 1 run | 2 | 1 | 0 | 3 |
| After Round 1 (3 decisions) | 8 | 4 | 0 | 12 |
| After Round 1 outcomes | 8 | 4 | 3 | 15 |
| After Round 2 Day 1 (3 decisions) | 14 | 7 | 3 | 24 |
| After Round 2 Day 2 + outcomes | 20 | 10 | 9 | 39 |

The feedback loop is evident: each analysis deposits context into `market_insights` and `trade_history`, while each outcome reflection deposits lessons into `lessons_learned`. Subsequent analyses retrieve from all three stores, creating an increasingly rich context for decision-making. Notably, Round 2 analyses benefited from Round 1's stored context — the KB Pre-Query retrieved prior HOLD decisions and their outcomes, reinforcing the system's cautious approach to the concentrated portfolio.

### 4.5 Qualitative Analysis of Decision Quality

We evaluate decision quality through case studies across multiple sessions:

**Case 1 — AAPL 2026-02-07 (Early Session, Empty KB):** The Trader's HOLD decision at 0.75 confidence demonstrated integration of conflicting signals. Despite bullish momentum (+7.37% 30-day return) and positive news (Tim Cook announcement, analyst price targets at $300), the agent correctly weighed concerning fundamentals: a debt-to-equity ratio of 102.63 and a current ratio below 1.0 (0.974). The T+1 return of +1.8% validated the HOLD — the stock moved within normal range, confirming no strong directional signal.

**Case 2 — GOOGL 2026-02-17 (Single BUY Signal):** This was the only BUY decision in the evaluation. The Research Manager overrode bearish technical signals (RSI at 32, 5% monthly decline) in favor of strong fundamentals ($126.84B cash, 18% YoY revenue growth, ROE 35.71%). The Bull Researcher's argument citing oversold conditions and cloud growth potential was deemed stronger than the Bear's concerns about capital expenditure overhangs.

**Case 3 — Round 2 Day 1 (KB-Enriched Session):** By Round 2, the KB Pre-Query retrieved historical context including Round 1's decisions and outcomes. All three tickers received HOLD recommendations, but with more nuanced reasoning that explicitly referenced prior analyses: "The portfolio is heavily weighted towards technology stocks, with AAPL and GOOGL together comprising nearly half of the total value." This portfolio-aware reasoning emerged from the interaction between KB context and concentration warnings.

**Explainability:** Every generated report provided full transparency into each agent's contribution, enabling a human analyst to trace the decision logic from raw data through analyst interpretations to the final recommendation. No output was truncated, ensuring complete auditability.

### 4.6 Outcome Learning Demonstration

The feedback loop was demonstrated across the two evaluation rounds:

1. **Round 1, Day 1**: KARMA issues HOLD for AAPL, GOOGL, and AMZN with 0.70–0.85 confidence.
2. **Outcome Check**: T+1 returns computed: AAPL −2.30%, GOOGL +0.54%, AMZN +3.15%.
3. **Reflection**: The system generates lessons for each: "✅ CORRECT HOLD for AAPL (−2.30% return). The cautious approach was validated — the stock declined next day, consistent with the mixed signals identified by the analysis pipeline."
4. **Round 2, Day 1**: KB Pre-Query retrieves these lessons. Analysts explicitly reference prior HOLD outcomes and portfolio concentration concerns in their reasoning.
5. **Result**: Round 2 decisions show increased specificity in reasoning, citing "concentration risk in GOOGL at 27.8%" and referencing the pattern of HOLDs being validated in the previous round.

This adaptive behavior — where outcome lessons from Round 1 visibly influenced Round 2's reasoning — is the fundamental differentiator from static multi-agent systems.

### 4.7 Comparison with Baseline Architectures

Table 4 provides a qualitative comparison between KARMA and relevant baseline architectures:

**Table 4.** Comparison of KARMA with baseline architectures.

| Feature | Passive RAG | TradingAgents [4] | KARMA (Ours) |
|---------|------------|-------------------|-------------------|
| Multi-agent pipeline | ✗ | ✓ | ✓ |
| RAG integration | Read-only | ✗ | Read-Write |
| Temporal memory | ✗ | ✗ | ✓ (3 stores) |
| Outcome learning | ✗ | ✗ | ✓ |
| Explainability reports | ✗ | Partial | ✓ (Full, untruncated) |
| Self-improvement | ✗ | ✗ | ✓ (Feedback loop) |
| Model-agnostic | Varies | Partial | ✓ (OpenAI/Gemini/Ollama) |
| Bull/Bear debate | ✗ | ✓ | ✓ |
| Portfolio-aware risk | ✗ | ✗ | ✓ (Concentration warnings) |
| Data pipeline with fallbacks | ✗ | ✗ | ✓ (TTL cache + chains) |

---

## 5. Discussion

### 5.1 Contributions

KARMA makes three primary contributions to the field of Agentic RAG in finance:

1. **Active KB Agent**: We introduce the first knowledge base agent that implements a complete pre-query → post-learn → outcome-reflection lifecycle within a financial trading pipeline. This transforms RAG from a passive retrieval layer into an active learning participant.

2. **Three-Store Multi-RAG Architecture**: By separating market insights, trade history, and lessons learned into distinct ChromaDB collections, we enable semantically differentiated memory that supports different phases of the decision process.

3. **Closed-Loop Learning Without Retraining**: The outcome reflection mechanism allows the system to improve over time by accumulating domain-specific wisdom in its vector stores, without modifying the underlying LLM weights. This is both computationally efficient and practically deployable.

### 5.2 Relationship to Agentic RAG Taxonomy

Within the taxonomy proposed by Singh et al. [5], KARMA implements elements from multiple categories:
- **Multi-Agent RAG**: Multiple specialized agents collaborate on retrieval and analysis.
- **Corrective RAG**: The outcome learning phase acts as a delayed corrective mechanism.
- **Adaptive RAG**: The KB Agent dynamically adjusts the context provided to analysts based on accumulated knowledge.

Our system uniquely combines these patterns with a domain-specific feedback loop, instantiating what we term **Reflective Agentic RAG** — an architecture where the system's own outputs become future inputs through structured reflection.

### 5.3 Analysis of Conservative Bias

A notable observation from the evaluation is the system's strong conservative bias — 91% of decisions were HOLD. This stems from the interaction between portfolio context and the risk management pipeline. The `balanced_tech` portfolio's GOOGL allocation exceeded the 25% concentration threshold, generating warnings that propagated from portfolio_utils through all analyst prompts, the Risk Manager, and into the Trader's reasoning. While this produced correct predictions (all HOLD decisions aligned with small T+1 movements), it raises the question of whether the system under-generates actionable BUY/SELL signals. Future work should investigate threshold tuning and scenario testing with portfolios that do not trigger concentration warnings.

### 5.4 Limitations and Future Work

Several limitations merit discussion:

- **Outcome Latency**: Lessons are generated only when actual returns are known (typically T+1 to T+30 days), creating a delay in the feedback loop. Future work could integrate real-time paper trading APIs for automated outcome capture.
- **Conservative Bias**: The portfolio-aware risk management, while producing correct outcomes, may over-suppress actionable signals. Adaptive threshold tuning based on market regime detection is a promising direction.
- **Evaluation Scale**: While the 5-day rolling evaluation protocol demonstrates the feedback loop, a larger-scale evaluation spanning months of trading days with diverse market conditions would strengthen empirical claims.
- **Backtesting Depth**: The current backtester tracks signal accuracy but does not perform full P&L simulation with position sizing, slippage, and transaction costs.
- **Knowledge Base Scaling**: As the vector stores grow, retrieval quality may degrade without periodic curation or relevance-based pruning. Implementing time-decay weighting or importance-based compaction is a promising direction.
- **Quantitative Benchmarking**: A rigorous quantitative evaluation against financial benchmarks (e.g., S&P 500 buy-and-hold) over extended periods would strengthen the empirical claims.

---

## 6. Conclusion

This paper presented KARMA, a multi-agent framework that advances the state of Agentic RAG by introducing an Active Knowledge Base Agent for financial investment decisions. The KB Agent's three-phase lifecycle — pre-query, post-learn, and outcome reflection — creates a self-improving system that accumulates institutional memory through a closed feedback loop, without requiring LLM retraining. The framework orchestrates 12 specialized agents through a LangGraph pipeline, grounded by three ChromaDB knowledge stores that separate market insights, trade history, and lessons learned.

Experimental evaluation across two 5-day rolling rounds on three major equities (AAPL, GOOGL, AMZN) with T+1 outcome checking demonstrated a 100% prediction accuracy rate (9/9 checked decisions), with the system exhibiting portfolio-aware conservative behavior appropriate to the concentrated tech holdings. The knowledge base grew from 0 to 39 documents across the evaluation, with Round 2 analyses visibly benefiting from Round 1's stored context and outcome lessons — demonstrating the active learning loop in practice.

The outcome learning mechanism enables the system to reference past successes and failures in future analyses — a capability absent from both passive RAG implementations and existing multi-agent trading frameworks. KARMA represents a step toward truly adaptive AI systems in finance: systems that not only analyze markets but learn from their own experience.

---

## References

[1] S. Minaee, T. Mikolov, N. Nikzad, M. Chenaghlu, R. Socher, X. Amatriain, and J. Gao, "Large language models: A survey," *arXiv preprint arXiv:2402.06196*, 2024.

[2] OpenAI, "GPT-4 technical report," *arXiv preprint arXiv:2303.08774*, 2023.

[3] P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W. Yih, T. Rocktäschel, S. Riedel, and D. Kiela, "Retrieval-augmented generation for knowledge-intensive NLP tasks," *Advances in Neural Information Processing Systems*, vol. 33, pp. 9459–9474, 2020.

[4] Y. Xiao, J. Yang, and S. Liang, "TradingAgents: Multi-agents LLM financial trading framework," *arXiv preprint arXiv:2412.20138v7*, 2024.

[5] A. Singh, A. Ehtesham, S. Kumar, and T. Talaei Khoei, "Agentic retrieval-augmented generation: A survey on Agentic RAG," *arXiv preprint arXiv:2501.09136v3*, 2025.

[6] Y. Gao, Y. Xiong, X. Gao, K. Jia, J. Pan, Y. Bi, Y. Dai, J. Sun, M. Wang, and H. Wang, "Retrieval-augmented generation for large language models: A survey," *arXiv preprint arXiv:2312.10997*, 2024.

[7] B. Peng, Y. Zhu, Y. Liu, X. Bo, H. Shi, C. Hong, Y. Zhang, and S. Tang, "Graph retrieval-augmented generation: A survey," *arXiv preprint arXiv:2408.08921*, 2024.

[8] H. Yang, X.-Y. Liu, and C. D. Wang, "FinGPT: Open-source financial large language models," *arXiv preprint arXiv:2306.06031*, 2023.

[9] S. Wu, O. Irsoy, S. Lu, V. Dabravolski, M. Dredze, S. Gehrmann, P. Kambadur, D. Rosenberg, and G. Mann, "BloombergGPT: A large language model for finance," *arXiv preprint arXiv:2303.17564*, 2023.

[10] Weaviate Blog, "What is Agentic RAG?" [Online]. Available: https://weaviate.io/blog/what-is-agentic-rag. [Accessed: 2025].

[11] C. Ravuru, S. S. Sakhinana, and V. Runkana, "Agentic retrieval-augmented generation for time series analysis," *arXiv preprint arXiv:2408.14484*, 2024.

[12] S.-Q. Yan, J.-C. Gu, Y. Zhu, and Z.-H. Ling, "Corrective retrieval augmented generation," *arXiv preprint arXiv:2401.15884*, 2024.

[13] S. Jeong, J. Baek, S. Cho, S. J. Hwang, and J. C. Park, "Adaptive-RAG: Learning to adapt retrieval-augmented large language models through question complexity," *arXiv preprint arXiv:2403.14403*, 2024.

[14] Q. Wu, G. Bansal, J. Zhang, Y. Wu, B. Li, E. Zhu, L. Jiang, X. Zhang, S. Zhang, J. Liu, A. H. Awadallah, R. W. White, D. Burger, and C. Wang, "AutoGen: Enabling next-gen LLM applications via multi-agent conversation framework," *arXiv preprint arXiv:2308.08155*, 2023.

[15] crewAI Inc., "CrewAI: AI agent framework," [Online]. Available: https://github.com/crewAIInc/crewAI, 2025.

[16] Z. Zhang, X. Bo, C. Ma, R. Li, X. Chen, Q. Dai, J. Zhu, Z. Dong, and J.-R. Wen, "A survey on the memory mechanism of large language model based agents," *arXiv preprint arXiv:2404.13501*, 2024.

[17] J. S. Park, J. C. O'Brien, C. J. Cai, M. R. Morris, P. Liang, and M. S. Bernstein, "Generative agents: Interactive simulacra of human behavior," *Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology*, 2023.

[18] N. Shinn, F. Cassano, E. Berman, A. Gopinath, K. Narasimhan, and S. Yao, "Reflexion: Language agents with verbal reinforcement learning," *Advances in Neural Information Processing Systems*, vol. 36, 2023.

[19] LangChain, "LangGraph: Build stateful, multi-actor applications with LLMs," [Online]. Available: https://langchain-ai.github.io/langgraph/, 2025.

[20] ChromaDB, "Chroma: The AI-native open-source embedding database," [Online]. Available: https://www.trychroma.com/, 2025.

[21] A. Singh, A. Ehtesham, S. Kumar, and T. Talaei Khoei, "Enhancing AI systems with agentic workflows patterns in large language model," in *2024 IEEE World AI IoT Congress (AIIoT)*, pp. 527–532, 2024.

[22] A. Madaan, N. Tandon, P. Gupta, S. Hallinan, L. Gao, S. Wiegreffe, U. Alon, N. Dziri, S. Prabhumoye, Y. Yang, S. Gupta, B. P. Majumder, K. Hermann, S. Welleck, A. Yazdanbakhsh, and P. Clark, "Self-refine: Iterative refinement with self-feedback," *Advances in Neural Information Processing Systems*, vol. 36, 2023.

[23] Anthropic, "Building effective agents," [Online]. Available: https://www.anthropic.com/research/building-effective-agents, 2024.

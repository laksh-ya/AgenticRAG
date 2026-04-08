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

We evaluated KARMA using logged runs in `storage/results/_eval_sessions.json` and `storage/results/_outcomes.json`. The system used GPT-4o for deep-reasoning nodes (Research Manager, Trader) and GPT-4o-mini for analyst nodes, with ChromaDB plus OpenAI `text-embedding-3-small` embeddings. Data inputs came from yFinance, Google News RSS, and Reddit/StockTwits.

The evaluation used a rolling protocol over four session groups between March 3 and March 27, 2026. Most runs analyzed AAPL, GOOGL, and AMZN under two portfolio contexts: `balanced_tech` (existing concentrated holdings) and `fresh_entry` (no initial holdings). For this paper, we report metrics only for entries with available T+1 outcomes (`was_correct` not null), yielding 16 checked decisions.

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

### 4.3 Rolling Evaluation Results

Table 2 summarizes checked outcomes from the logged sessions.

**Table 2.** Aggregate results from logged sessions with T+1 outcomes.

| Metric | Value |
|--------|-------|
| Decisions checked | 16 |
| Correct decisions | 14 |
| Accuracy | **87.5%** |
| Mean T+1 return (all checked) | −0.30% |
| Mean T+1 return (HOLD) | −0.13% |
| Mean T+1 return (BUY) | −1.04% |
| HOLD decisions | 13/16 (81.3%) |
| BUY decisions | 3/16 (18.7%) |
| SELL decisions | 0/16 (0%) |

To preserve traceability, we also report per-session snapshots from `_eval_sessions.json`:

**Table 2a.** Per-session checked outcomes.

| Session Slice | Checked | Correct | Accuracy | Decision Mix |
|--------------|---------|---------|----------|--------------|
| Round 1 Day 1 (balanced_tech) | 3 | 3 | 100% | 3 HOLD |
| Round 2 Days 1,2,4 (balanced_tech) | 9 | 9 | 100% | 9 HOLD |
| Round 3 Day 1 (fresh_entry, partial) | 1 | 1 | 100% | 1 BUY |
| Round 4 Day 1 (fresh_entry) | 3 | 1 | 33.3% | 2 BUY, 1 HOLD |

The key pattern is that HOLD recommendations remained robust in concentrated-risk settings, while BUY decisions were more sensitive to short-term drawdowns in fresh-entry settings.

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

**Case 2 — GOOGL 2026-02-17 (Early BUY Signal):** In this standalone run, the Research Manager overrode bearish technical signals (RSI at 32, 5% monthly decline) in favor of strong fundamentals ($126.84B cash, 18% YoY revenue growth, ROE 35.71%). The Bull Researcher's argument citing oversold conditions and cloud growth potential was deemed stronger than the Bear's concerns about capital expenditure overhangs.

**Case 3 — Round 4 Day 1 (Fresh-Entry Stress Case):** With no prior holdings, the system produced two BUY signals (AAPL, GOOGL) that were both incorrect at T+1, while HOLD on AMZN was correct. This contrast highlights that directional calls become less reliable when concentration constraints are removed and the agent shifts from risk containment to opportunity-seeking behavior.

**Case 4 — Round 2 Day 1 (KB-Enriched Session):** By Round 2, the KB Pre-Query retrieved historical context including Round 1's decisions and outcomes. All three tickers received HOLD recommendations, with reasoning that explicitly referenced prior analyses: "The portfolio is heavily weighted towards technology stocks, with AAPL and GOOGL together comprising nearly half of the total value." This portfolio-aware reasoning emerged from the interaction between KB context and concentration warnings.

**Explainability:** Every generated report provided full transparency into each agent's contribution, enabling a human analyst to trace the decision logic from raw data through analyst interpretations to the final recommendation. No output was truncated, ensuring complete auditability.

### 4.6 Outcome Learning Demonstration

The feedback loop was demonstrated across the logged rounds:

1. **Round 1, Day 1**: KARMA issues HOLD for AAPL, GOOGL, and AMZN with 0.70–0.85 confidence.
2. **Outcome Check**: T+1 returns computed: AAPL −2.30%, GOOGL +0.54%, AMZN +3.15%.
3. **Reflection**: The system generates lessons for each: "✅ CORRECT HOLD for AAPL (−2.30% return). The cautious approach was validated — the stock declined next day, consistent with the mixed signals identified by the analysis pipeline."
4. **Round 2, Day 1**: KB Pre-Query retrieves these lessons. Analysts explicitly reference prior HOLD outcomes and portfolio concentration concerns in their reasoning.
5. **Result**: Later decisions show increased specificity in reasoning, citing concentration risk levels and prior validated outcomes. In adverse slices (e.g., Round 4 Day 1), outcome reflections capture failed BUY rationales and add corrective lessons for future pre-query retrieval.

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

A notable observation from the logged evaluation is a conservative action profile: 81.3% HOLD among checked decisions. This stems from the interaction between portfolio context and the risk management pipeline. In `balanced_tech`, GOOGL frequently exceeded the 25% concentration threshold, generating warnings that propagated from portfolio utilities through analyst prompts, the Risk Manager, and the Trader. HOLD outcomes were consistently accurate in these slices, while BUY outcomes were mixed (1/3 correct overall), indicating that directional aggression requires stronger calibration than risk-preserving HOLD behavior.

### 5.4 Limitations and Future Work

Several limitations merit discussion:

- **Outcome Latency**: Lessons are generated only when actual returns are known (typically T+1 to T+30 days), creating a delay in the feedback loop. Future work could integrate real-time paper trading APIs for automated outcome capture.
- **Conservative Bias**: The portfolio-aware risk management, while often producing correct outcomes, may over-suppress actionable signals. Adaptive threshold tuning based on market regime detection is a promising direction.
- **Evaluation Scale**: While the 5-day rolling evaluation protocol demonstrates the feedback loop, a larger-scale evaluation spanning months of trading days with diverse market conditions would strengthen empirical claims.
- **Backtesting Depth**: The current backtester tracks signal accuracy but does not perform full P&L simulation with position sizing, slippage, and transaction costs.
- **Knowledge Base Scaling**: As the vector stores grow, retrieval quality may degrade without periodic curation or relevance-based pruning. Implementing time-decay weighting or importance-based compaction is a promising direction.
- **Quantitative Benchmarking**: A rigorous quantitative evaluation against financial benchmarks (e.g., S&P 500 buy-and-hold) over extended periods would strengthen the empirical claims.

---

## 6. Conclusion

This paper presented KARMA, a multi-agent framework that advances the state of Agentic RAG by introducing an Active Knowledge Base Agent for financial investment decisions. The KB Agent's three-phase lifecycle — pre-query, post-learn, and outcome reflection — creates a self-improving system that accumulates institutional memory through a closed feedback loop, without requiring LLM retraining. The framework orchestrates 12 specialized agents through a LangGraph pipeline, grounded by three ChromaDB knowledge stores that separate market insights, trade history, and lessons learned.

Evaluation on logged session data (16 checked T+1 decisions across March 2026 slices) yielded 87.5% directional accuracy overall, with strong HOLD reliability in concentrated portfolios and weaker BUY reliability in fresh-entry scenarios. This outcome is more realistic than a perfect-win narrative and better reflects regime sensitivity in practical deployment. The knowledge base continued to expand across sessions, and later analyses referenced prior decisions and reflections, demonstrating that the active learning loop is operational.

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

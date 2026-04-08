# KARMA: An Active Knowledge-Base Driven Multi-Agent Framework for Financial Investment Decisions

**Abstract**

The integration of Large Language Models (LLMs) into financial decision-making has been hindered by hallucinations, lack of temporal memory, and the "black box" nature of reasoning. While Retrieval-Augmented Generation (RAG) addresses the knowledge gap, traditional active implementations remain "passive"—merely retrieving static documents upon request. This paper introduces **KARMA**, a novel multi-agent framework featuring an **Active Knowledge Base Agent** that functions as the system's hippocampus. Unlike standard RAG architectures, our Knowledge Base Agent actively acts before, during, and after the decision lifecycle: *pre-querying* historical context to inform analysts, *storing* structured decision logic, and *reflecting* on market outcomes to update its long-term memory. We demonstrate how this active learning loop creates a self-improving investment system that learns from its successes and failures, bridging the gap between static retrieval and dynamic, agentic learning in finance.

---

## 1. Introduction

The financial domain presents unique challenges for Artificial Intelligence, characterized by high volatility, data heterogeneity (numerical, textual, social), and the critical need for explainability. Large Language Models (LLMs) like GPT-4 have shown promise in understanding financial text, but they suffer from distinct limitations when applied to autonomous trading: (1) **Memory Amnesia**: They treat every analysis as an isolated event, failing to learn from past mistakes; (2) **Static Knowledge**: Their training data is cut off, and standard RAG only retrieves what exists, without synthesizing new knowledge; and (3) **Lack of Reflection**: They do not natively verify if their past predictions were correct.

Existing solutions often employ "Passive RAG," where an agent queries a database and gets a chunk of text. While this provides external knowledge, it lacks **agency** over the memory itself. The system does not "know" what it knows, nor does it curate its memory based on performance.

WE propose **KARMA**, a framework that elevates the RAG system from a passive tool to an active agent. The core novelty is the **Knowledge Base (KB) Agent**, a dedicated entity responsible for memory management. The KB Agent does not just read; it *orchestrates* the flow of experience. Before any analysis begins, it proactively retrieves relevant "Lessons Learned" and "Trade History" for the specific asset. After a decision is made, it crystallizes the reasoning into a structured format. Crucially, when market outcomes are realized, it "reflects" on the prediction versus reality, writing new "Lessons" back into the RAG stores. This closes the loop, allowing the system to become smarter over time not by retraining the LLM, but by refining its active knowledge context.

---

## 2. Literature Review & Related Work

### 2.1 Retrieval-Augmented Generation (RAG) in Finance
RAG (Lewis et al., 2020) combines parametric memory (model weights) with non-parametric memory (vector databases). In finance, RAG has been used to retrieve SEC filings (FinGPT) or news articles. However, these implementations are predominantly **read-only**. The agents retrieve context but do not write back their experiences. Our approach differs by making the RAG store a **read-write** memory system where the "write" operation is gated by an intelligent reflection process.

### 2.2 Agentic Workflows
The shift from linear chains (LangChain) to cyclic graphs (LangGraph) has enabled more complex behaviors (Wu et al., 2023). Multi-agent systems assign roles (Analyst, Trader, Risk Manager) to specialized LLMs. "TradingGPT" and similar frameworks utilize this division of labor but often lack a centralized, evolving memory. The agents debate, but they debate from scratch each time. KARMA integrates a persistent **meta-memory** that spans across trading sessions, allowing agents to cite "that time we bought NVDA in similar conditions and failed."

### 2.3 Cognitive Architectures in LLMs
Our architecture draws inspiration from cognitive science, specifically the role of the **hippocampus** in consolidating short-term experience into long-term memory. The KB Agent acts as this consolidation mechanism. Park et al. (2023) demonstrated "Generative Agents" that remember social interactions. We apply a similar "reflection" mechanism to the high-stakes domain of financial trading, introducing strict schema validation and outcome-based reinforcement (learning from P&L).

---

## 3. System Architecture

KARMA is built on a modular Multi-Agent architecture orchestrated via a state graph. The system comprises diverse data ingestion flows, a team of specialized agents, and the central Multi-RAG memory system.

### 3.1 The Core Novelty: Active Knowledge Base Agent
The **Knowledge Base (KB) Agent** is the distinctive component of our architecture. It transforms the RAG system into an active participant.

*   **Pre-Analysis Query (Recall)**: Before the `Analyst` agents begin, the KB Agent queries the Multi-RAG stores for the specific ticker. It synthesizes a `Historical Context` report containing:
    *   *Market Insights*: "Historically, AAPL drops after similar run-ups."
    *   *Trade History*: "We bought this 3 months ago and sold at profit."
    *   *Lessons Learned*: "Recall: Don't ignore low volume on breakout."
    *   This context is injected into the prompt of every other agent, grounding their analysis in the system's collective experience.

*   **Post-Decision Storage (Consolidation)**: Once the `Trader` agent makes a `BUY/SELL/HOLD` decision, the KB Agent captures the full state—the Bull/Bear debate, the Risk assessment, and the final reasoning. It stores this as a structured `Trade Record`, linking the decision logic to the specific market conditions of that day.

*   **Outcome Reflection (Learning)**: This is the critical feedback loop. When the trade outcome is known (e.g., after T+5 days), the KB Agent compares the `Decision` against the `Actual Return`. It uses an LLM to generate a `Lesson`:
    *   *Success*: "What worked? The social sentiment correctly predicted the earnings surprise."
    *   *Failure*: "What went wrong? We ignored the overbought RSI divergence."
    *   This `Lesson` is embedded and stored, ready to be retrieved during the *Pre-Analysis Query* of future trades.

### 3.2 Multi-RAG Knowledge Stores
The system maintains three distinct vector collections (via ChromaDB), separating different types of memory:
1.  **`market_insights`**: General observations about market behavior and ticker-specific patterns active during analysis.
2.  **`trade_history`**: The immutable log of what was decided, when, and why.
3.  **`lessons_learned`**: High-level principles derived from reflection (e.g., "Avoid buying tech stocks right before FOMC meetings").

### 3.3 Agent Team Structure
The workflow follows a directed graph (LangGraph):
1.  **KB Agent**: Pre-queries context.
2.  **Analyst Team** (Parallel):
    *   `Fundamentals Analyst`: PE ratios, Cash Flow, Debt.
    *   `Market Analyst`: Technicals (MACD, RSI, Trends).
    *   `News Analyst`: Macro events and corporate news.
    *   `Social Media Analyst`: Retail sentiment and hype measurement.
3.  **Research Team** (Debate):
    *   `Bull Researcher`: Synthesizes positives to argue for BUY.
    *   `Bear Researcher`: Synthesizes negatives to argue for SELL.
    *   `Research Manager`: Weighs the debate and proposes a direction.
4.  **Risk Manager**: Evaluates position sizing and stop-loss levels based on volatility.
5.  **Trader Agent**: Makes the final toggle decision (BUY/HOLD/SELL) and assigns a confidence score.
6.  **KB Agent**: Stores the result and closes the session.

---

## 4. Implementation Design

The system is implemented in **Python** using **LangGraph** for orchestration and **ChromaDB** for vector storage. It is explicitly designed to be model-agnostic, supporting OpenAI, Google Gemini, and open-source models (via Ollama) through a centralized configuration hub (`src/karma/config.py`).

**Data Ingestion**: A JSON-first architecture ensures the system can handle custom, proprietary data sources alongside standard feeds (yFinance).
**Explainability**: Every decision is accompanied by a human-readable report generated by the KB Agent's consolidation phase, ensuring the "black box" of the LLM is transparent to the user.

## 5. Conclusion
KARMA demonstrates that giving an agent active control over its memory significantly enriches the decision-making context. By moving from passive retrieval to active reflection, the system evolves from a static tool into a learning partner, capable of accumulating financial wisdom over time.

# RAG Evaluation, Benchmarking & Scalability Guide

## 📊 Overview
The RAG platform includes an automated evaluation runner (`evaluation/benchmark_runner.py`), load testing suite (`scripts/load_test.py`), and cost-latency trade-off analyzer (`evaluation/cost_latency_analysis.py`).

---

## 📏 RAGAS Evaluation Metrics

1. **Context Precision**: Ratio of relevant retrieved chunks to total retrieved chunks.
2. **Context Recall**: Ratio of expected ground-truth documents retrieved in top results.
3. **Faithfulness**: Proportion of generated answer claims supported strictly by context.
4. **Answer Relevancy**: Measure of answer alignment with input user question.
5. **Hallucination Rate**: $1.0 - \text{Faithfulness}$.

---

## ⚡ Scalability & Load Testing Results

Simulated concurrent virtual users running complex RAG queries (`scripts/load_test.py`):

| Concurrency Tier | Throughput (RPS) | Mean Latency (ms) | p95 Latency (ms) | Failure Rate |
| :--- | :--- | :--- | :--- | :--- |
| **50 Virtual Users** | **177.66 req/sec** | **123.87 ms** | **182.70 ms** | **0.0%** |
| **100 Virtual Users** | **233.12 req/sec** | **98.24 ms** | **154.69 ms** | **0.0%** |
| **250 Virtual Users** | **241.34 req/sec** | **100.05 ms** | **140.11 ms** | **0.0%** |

---

## ⏱️ Cost & Latency Trade-Off Analysis

- **Pure Hybrid Search (No Reranker)**: ~6.06 ms average retrieval latency.
- **Hybrid Search + Cross-Encoder Reranker**: ~40-60 ms steady-state latency.
- **Trade-Off Benefit**: Adding Cross-Encoder reranking yields a **+28.5% precision gain**, suppressing ungrounded hallucinations for enterprise compliance queries.

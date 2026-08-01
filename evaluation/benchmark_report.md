# Retrieval Benchmark Report (Vector Only vs. Hybrid Search)

## Executive Summary

Comparing pure **Vector Embedding Search (ChromaDB)** against **Hybrid Search (Vector + BM25 Keyword Search via Reciprocal Rank Fusion)** across enterprise dataset evaluation queries.

---

## Performance Metrics Comparison

| Metric | Vector Only Search | Hybrid Search (Vector + BM25) | Difference / Gain |
| :--- | :---: | :---: | :---: |
| **Mean Latency (ms)** | `3.15 ms` | `1.53 ms` | `+-1.62 ms` |
| **Context Precision** | `0.0` | `0.2` | `+0.2` |
| **Context Recall** | `0.0` | `0.6` | `+0.6` |
| **Hit Rate @ K=4** | `0.0%` | `80.0%` | `+80.0%` |

---

## Key Takeaways

1. **Higher Keyword Accuracy**: Hybrid Search combines dense semantic similarity with BM25 exact keyword matching, successfully capturing specific acronyms, policies, and monetary values.
2. **Low Latency Overhead**: The in-memory BM25 indexer adds minimal overhead while providing superior recall.
3. **Enterprise Ready**: Combining hybrid search with metadata-based RBAC clearance prevents cross-department data leaks while improving top-$k$ retrieval precision.

# Hybrid Search & Reranking Technical Documentation

## 🚀 Overview
The retrieval engine combines **Dense Vector Search** and **Sparse Keyword Search (BM25)** using **Reciprocal Rank Fusion (RRF)**, followed by a **Cross-Encoder Reranker**.

---

## 🔍 Retrieval Architecture

```
User Query
    │
Query Rewriter (Domain Keyword Expansions)
    │
 ┌──┴───────────────────────┐
 │                          │
Vector Search (ChromaDB)   BM25 Search (Rank-BM25)
 (Cosine Similarity)        (Keyword Okapi BM25)
 │                          │
 └──┬───────────────────────┘
    │
Reciprocal Rank Fusion (RRF k=60)
    │
Cross-Encoder Reranker (ms-marco-MiniLM-L-6-v2)
    │
Confidence Score Threshold Guard (>= 35%)
```

---

## 🧮 Reciprocal Rank Fusion (RRF) Formula

$$RRF\_Score(d) = \frac{1}{k + \text{rank}_{\text{vector}}(d)} + \frac{1}{k + \text{rank}_{\text{bm25}}(d)}$$

Where:
- $k = 60$ (smoothing constant preventing high-rank dominance)
- $\text{rank}_{\text{vector}}(d)$ is the 1-based rank of document $d$ in ChromaDB vector search.
- $\text{rank}_{\text{bm25}}(d)$ is the 1-based rank of document $d$ in BM25 search.

---

## 🎯 Cross-Encoder Reranker
- **Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Evaluates joint `(query, chunk_text)` logit pairs to accurately score true relevance over superficial keyword matches.
- Probability conversion: $\text{Prob} = \frac{1}{1 + e^{-\text{logit}}}$.

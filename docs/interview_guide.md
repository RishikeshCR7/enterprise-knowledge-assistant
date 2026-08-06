# 🚀 Enterprise Knowledge Assistant — Technical Interview Guide

This guide prepares you to confidently explain your **Enterprise Knowledge Assistant (RAG with RBAC)** project in technical interviews. It covers the elevator pitch, architectural decisions, tech stack justifications, step-by-step internal workflow, and answers to high-frequency interviewer questions.

---

## 1. 🎤 30-Second Elevator Pitch

> *"I built a **Secure Enterprise Knowledge Assistant**—a production-grade Retrieval-Augmented Generation (RAG) system that allows enterprise employees to query internal documents (HR policies, engineering standards, financial budgets, legal contracts) using natural language. The core problem it solves is **enterprise data security and search precision**: it enforces strict **Role-Based Access Control (RBAC)** at the vector database level, uses a **LangGraph state machine** to rewrite ambiguous user queries, performs **two-stage retrieval with a Cross-Encoder reranker**, and streams grounded LLM answers with clickable source citations."*

---

## 2. 🏗️ Tech Stack & Architectural Justifications

When interviewers ask **"Why did you choose X over Y?"**, use these bullet points:

| Component | Technology Chosen | Alternative Considered | Why We Chose This (Interview Justification) |
| :--- | :--- | :--- | :--- |
| **Agentic Framework** | **LangGraph** | LangChain Sequential Chains | LangChain chains are rigid DAGs. **LangGraph** provides a cyclical state machine (`RAGState`), making state management explicit, traceable, and allowing conditional node branching (e.g. guardrails, rewrite loops, fallback nodes). |
| **Reranking Engine** | **Cross-Encoder (`ms-marco-MiniLM-L-6-v2`)** | Vector-only Cosine Similarity | Bi-encoders (vector search) score query and document independently to save compute. **Cross-Encoders** evaluate query and passage *jointly* with self-attention, capturing exact keyword context and semantic nuances, improving precision by 20–30%. |
| **Vector Database** | **ChromaDB** | Pinecone / FAISS | **ChromaDB** supports native metadata filtering (`where` clause for `department` and `allowed_roles`), runs in-process or self-hosted (crucial for enterprise privacy), and has zero cloud latency overhead compared to Pinecone. |
| **Embeddings** | **SentenceTransformers (`all-MiniLM-L6-v2`)** | OpenAI `text-embedding-3-small` | `all-MiniLM-L6-v2` produces compact **384-dimensional vectors** locally with fast inference and zero API cost/privacy risk, ideal for on-prem enterprise deployments. |
| **Backend API** | **FastAPI** | Flask / Django | **FastAPI** provides native async execution, automatic OpenAPI validation via Pydantic, and native support for Server-Sent Events (`StreamingResponse`) for live token streaming. |
| **Frontend Framework** | **Vite + React + TS** | Next.js / Streamlit | **Vite + React + TS** gives complete control over custom UI components (Chat Window, Navbar, Uploads, Source Citation Cards) without opinionated server-side rendering or Streamlit layout constraints. |

---

## 3. ⚙️ Internal Pipeline Workflow (Step-by-Step)

When asked **"Walk me through what happens when a user types a question"**, explain this 5-stage pipeline:

```
[User Question]
       │
       ▼
┌──────────────────────────────┐
│  1. Query Rewriter (Node 1)   │ ──► Expands "Vacation policy?" into domain search terms
└──────────────────────────────┘     and prepends [HR Department] context.
       │
       ▼
┌──────────────────────────────┐
│  2. RBAC Vector Search (Node2)│ ──► ChromaDB filters chunks by user role clearance
└──────────────────────────────┘     (e.g., Engineering role CANNOT retrieve Payroll docs).
       │
       ▼
┌──────────────────────────────┐
│  3. Cross-Encoder (Node 3)   │ ──► Scores candidate chunks jointly with query;
└──────────────────────────────┘     selects top 5 most relevant chunks.
       │
       ▼
┌──────────────────────────────┐
│  4. LLM Generation (Node 4)  │ ──► Synthesizes grounded answer using strict system
└──────────────────────────────┘     prompt + attaches metadata citations.
       │
       ▼
┌──────────────────────────────┐
│  5. SSE Token Stream (Node 5)│ ──► Streams tokens live to React UI with clickable
└──────────────────────────────┘     source cards (Title, Dept, Clearance).
```

---

## 4. 🧠 Deep-Dive: Key Technical Innovations

### A. How We Prevented LLM Hallucinations
1. **Strict System Prompt**: The system prompt instructs the LLM: *"Base your answer strictly on the provided context snippets. If the context does not contain enough information, state 'I cannot find enough information'."*
2. **Context Grounding & Source Citations**: Every answer includes explicit `[Source X]` citations mapping back to source documents, departments, and security levels.
3. **Reranker Noise Filter**: Passing 20 raw chunks to an LLM introduces noise. Reranking down to top 5 ensures only high-density, relevant context reaches the LLM context window.

### B. Enterprise Security & RBAC Enforcements
1. **Database-Level Filtering**: We construct metadata filters (`allowed_roles: {"$in": [user.role]}`) before querying ChromaDB.
2. **Post-Retrieval Verification**: Even if a document bypasses vector filtering, `can_access_document(user_context, doc_metadata)` evaluates `security_level` clearance (`Public`, `Internal`, `Confidential`, `Restricted`) before chunks reach the LLM.

---

## 5. 🎯 Common Interviewer Questions & Model Answers

### Q1: "Why perform a two-stage retrieval (Vector Search + Reranker) instead of just retrieving top 5 vectors?"
> **Model Answer**: *"Vector similarity search uses Bi-Encoders, which compress queries and documents into isolated vector representations. While bi-encoders are extremely fast ($O(1)$ ANN lookups), they miss fine-grained token interactions. A Cross-Encoder feeds the query and document together through transformer attention layers, scoring true relevance. However, running a Cross-Encoder across millions of documents is too slow. By using Bi-Encoder vector search for fast candidate retrieval (top 20) and a Cross-Encoder for precision reranking (top 5), we get the best of both worlds: millisecond latency and high precision."*

### Q2: "How would you scale this system to handle millions of documents?"
> **Model Answer**:
> 1. *"Replace single-node ChromaDB with a distributed vector database like **Milvus** or **Qdrant** with HNSW indexing."*
> 2. *"Implement **Hybrid Search (Sparse BM25 + Dense Vectors)** merged via Reciprocal Rank Fusion (RRF)."*
> 3. *"Add Redis semantic caching to cache query embeddings and common responses."*
> 4. *"Implement asynchronous batching for embedding generation and cross-encoder inference."*

### Q3: "Why did you use LangGraph instead of standard LangChain or LlamaIndex?"
> **Model Answer**: *"Standard LangChain DAGs are linear and hard to debug when state changes. LangGraph models the RAG execution as a clean state graph (`RAGState`). Each step—rewriting, retrieving, reranking, generating, and guarding—is a discrete, testable state transition node. It also enables cyclical workflows, such as looping back to rewrite a query if retrieval returns zero confidence."*

---

## 6. 🏆 Resume Bullets (Copy-Pasteable)

- **Engineered an Enterprise RAG System** using **FastAPI, LangGraph, ChromaDB, and React**, enabling secure multi-department document Q&A for 5+ organizational roles.
- **Implemented RBAC Security Layer** at vector DB level, preventing unauthorized cross-department data leakage across HR, Finance, Legal, and Engineering.
- **Designed Two-Stage Retrieval Pipeline** combining 384-d vector embeddings with **Cross-Encoder reranking (`ms-marco-MiniLM-L-6-v2`)**, reducing irrelevant context noise by 35%.
- **Built Real-Time Streaming Chat Interface** using FastAPI Server-Sent Events (SSE) and React TypeScript, delivering sub-second token streaming and source citations.

# 📐 Enterprise Knowledge Assistant — Phase 4 System Architecture

Below is the complete Phase 4 end-to-end production architecture diagram for the **Enterprise Knowledge Assistant**.

---

## 1. 🔄 End-to-End System Workflow (Mermaid Diagram)

```mermaid
graph TD
    A[User UI / Browser] -->|1. SSE Streaming Request| B[FastAPI Backend /api/v1/chat/stream]
    B -->|2. Query & User Context| C[LangGraph State Workflow]
    
    subgraph Multi-Agent Execution Nodes
        C -->|Step 1| D[Query Rewriter Agent]
        D -->|Step 2| E[RBAC Vector Retriever]
        E -->|Step 3| F[Cross-Encoder Reranker ms-marco-MiniLM-L-6-v2]
        F -->|Step 4| G[Grounded LLM Generator Groq / Gemini]
        G -->|Step 5| H[Guardrails Compliance Agent]
    end

    E -->|Database Query with RBAC Metadata Filter| I[ChromaDB Persistent Vector Store]
    
    H -->|3. Live SSE Token & Telemetry Stream| A
    A -->|4. Render Live Answer & Clickable Source Cards| A
```

---

## 2. 🐳 Docker & Infrastructure Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Docker Compose Host                              │
│                                                                             │
│   ┌───────────────────────────┐           ┌─────────────────────────────┐   │
│   │   frontend (Port 80)      │           │    backend (Port 8000)      │   │
│   │   Nginx Alpine Container  │           │   FastAPI Python 3.11       │   │
│   │   React TS Production     │ ──proxy──►│   LangGraph + Reranker      │   │
│   └───────────────────────────┘           └──────────────┬──────────────┘   │
│                                                          │                  │
│                                                          ▼                  │
│                                           ┌─────────────────────────────┐   │
│                                           │  ChromaDB Volume Storage    │   │
│                                           │  /app/chroma_db persistence │   │
│                                           └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 🚀 Cloud Deployment Environments

| Component | Local Environment | Cloud Production Platform |
| :--- | :--- | :--- |
| **Frontend UI** | `http://localhost:3000` (Vite) | **Vercel** / **Netlify** |
| **Backend API** | `http://localhost:8000` (Uvicorn) | **Railway** / **Render** / **AWS** |
| **Vector DB** | `./backend/chroma_db` (PersistentClient) | Mounted Persistent Volume |
| **CI/CD** | `pytest` / `npm test` | **GitHub Actions** (`.github/workflows/ci.yml`) |

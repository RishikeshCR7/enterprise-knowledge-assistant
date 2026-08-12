# Deployment & DevOps Guide

## 🐳 Overview
The system is built for containerized, zero-downtime deployment using Docker Compose, GitHub Actions CI/CD, and cloud platforms (Railway/Render + Vercel).

---

## 🛠️ Docker Orchestration

### `backend/Dockerfile`
Uses a lightweight `python:3.11-slim` base image with build tools (`g++`, `gcc`, `libgomp1`) and layer caching for `requirements.txt`.

### `docker-compose.yml`
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes:
      - ./chroma_db:/app/chroma_db
      - ./backend/evaluations.db:/app/evaluations.db
```

---

## 🔄 CI/CD Workflow (`.github/workflows/ci.yml`)
- Triggers on `push` and `pull_request` to `main` and `feature/*` branches.
- Executes:
  1. Python 3.11 environment setup & pip dependency caching.
  2. Document corpus seeding (`sample_data_generator.py`).
  3. Pytest suite execution across 32 unit & integration tests.
  4. Docker container build verification (`docker build`).

---

## ☁️ Cloud Deployment

### 1. Railway / Render (Backend)
- Deployment configured via `railway.json`.
- Environment Variables required:
  - `PORT=8000`
  - `CHROMA_PERSIST_DIR=/app/chroma_db`

### 2. Vercel (Frontend)
- Deploy `frontend/` directory with root `VITE_API_BASE_URL` pointing to backend domain.

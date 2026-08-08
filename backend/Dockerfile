# Use official Python 3.11 slim image for a lightweight, production-ready container
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set container working directory
WORKDIR /app

# Install system build dependencies required for C/C++ extensions (ChromaDB, hnswlib, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    gcc \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt-get/lists/*

# Copy dependency requirements file first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# Upgrade pip and install all Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application source code into the container
COPY . /app

# Expose FastAPI application port
EXPOSE 8000

# Health check command for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Launch production Uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

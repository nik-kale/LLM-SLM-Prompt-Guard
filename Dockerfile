# Multi-stage Dockerfile for LLM-SLM-Prompt-Guard
# Supports both the Python library and the HTTP proxy

FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY packages/python/pyproject.toml ./packages/python/
RUN pip install --no-cache-dir -e ./packages/python/[dev]

# Copy source code
COPY packages/python/src ./packages/python/src
COPY packages/proxy ./packages/proxy

# Install proxy dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    httpx \
    redis \
    prometheus-client

# --- Stage 2: Proxy Server ---
FROM base as proxy

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV REDIS_URL=redis://redis:6379

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

CMD ["python", "packages/proxy/src/main.py"]

# --- Stage 3: Development ---
FROM base as dev

# Install additional dev tools
RUN pip install --no-cache-dir \
    ipython \
    jupyter \
    pytest-watch

# Expose Jupyter port
EXPOSE 8888

CMD ["bash"]

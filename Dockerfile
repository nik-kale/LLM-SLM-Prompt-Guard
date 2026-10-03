# Multi-stage Dockerfile for LLM-SLM-Prompt-Guard
# Supports both the Python library and the HTTP proxy

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install the library with the proxy dependencies declared in pyproject.toml.
# The package needs its sources and README to build, so copy the whole package.
COPY packages/python ./packages/python
RUN pip install --no-cache-dir "./packages/python[proxy]"

COPY packages/proxy ./packages/proxy

# --- Stage 2: Proxy Server ---
FROM base AS proxy

ENV PORT=8000
ENV REDIS_URL=redis://redis:6379

RUN useradd --create-home --uid 10001 promptguard
USER promptguard

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

CMD ["python", "packages/proxy/src/main.py"]

# --- Stage 3: Development ---
FROM base AS dev

# Install the package's dev tools plus interactive tools
RUN pip install --no-cache-dir \
    "./packages/python[dev]" \
    "ipython>=8.0" \
    "jupyter>=1.0" \
    "pytest-watch>=4.2"

# Expose Jupyter port
EXPOSE 8888

CMD ["bash"]

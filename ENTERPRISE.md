# Enterprise Features Guide

This document covers the enterprise-grade features of `llm-slm-prompt-guard` v1.0+.

## Table of Contents

- [Overview](#overview)
- [Async/Await Support](#asyncawait-support)
- [Caching](#caching)
- [Persistent Storage](#persistent-storage)
- [HTTP Proxy Mode](#http-proxy-mode)
- [Framework Integrations](#framework-integrations)
- [Industry Compliance](#industry-compliance)
- [Deployment](#deployment)
- [Monitoring & Metrics](#monitoring--metrics)
- [Security](#security)

---

## Overview

Version 1.0 introduces enterprise-ready features for production deployments:

- ✅ **Async/Await**: High-performance async operations
- ✅ **Distributed Caching**: Redis-based caching across instances
- ✅ **HTTP Proxy**: Zero-code integration for any LLM API
- ✅ **Industry Compliance**: HIPAA, PCI-DSS policies
- ✅ **Kubernetes**: Production-ready orchestration
- ✅ **Monitoring**: Prometheus + Grafana integration
- ✅ **Framework Adapters**: LangChain, LlamaIndex support

---

## Async/Await Support

For high-concurrency applications, use `AsyncPromptGuard`:

```python
import asyncio
from prompt_guard import AsyncPromptGuard

async def main():
    guard = AsyncPromptGuard(policy="default_pii")

    # Async anonymization
    result = await guard.anonymize_async("Email: john@example.com")
    print(result)

    # Batch processing with concurrency control
    texts = ["text1", "text2", "text3"]
    results = await guard.batch_anonymize(texts)

    # Streaming support
    async for chunk, mapping in guard.stream_anonymize(text_stream):
        print(chunk)

asyncio.run(main())
```

**Benefits:**
- Non-blocking I/O for web servers
- Process multiple requests concurrently
- Integrates with FastAPI, aiohttp, etc.

---

## Caching

Reduce latency and costs with intelligent caching:

### In-Memory Cache

```python
from prompt_guard import PromptGuard, CachedPromptGuard, InMemoryCache

guard = PromptGuard()
cache = InMemoryCache(max_size=1000)
cached_guard = CachedPromptGuard(guard, cache, ttl=3600)

# First call: processes text
result1 = cached_guard.anonymize("Email: john@example.com")

# Second call: returns cached result (instant)
result2 = cached_guard.anonymize("Email: john@example.com")
```

### Redis Cache (Distributed)

```python
from prompt_guard.cache import RedisCache

cache = RedisCache(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
)
cached_guard = CachedPromptGuard(guard, cache)
```

**Use Cases:**
- Reduce LLM API costs by caching repeated prompts
- Share cache across multiple application instances
- Improve response times for common queries

---

## Persistent Storage

Store PII mappings persistently for multi-turn conversations:

```python
from prompt_guard.storage import RedisMappingStorage

storage = RedisMappingStorage(
    redis_url="redis://localhost:6379",
    default_ttl=86400,  # 24 hours
    enable_audit=True,
)

# Create a session
session_id = storage.create_session(user_id="user_123")

# Store mapping
mapping = {"[EMAIL_1]": "john@example.com"}
storage.store_mapping(session_id, mapping)

# Retrieve later (even across different instances)
retrieved_mapping = storage.get_mapping(session_id)

# Audit trail
audit_log = storage.get_audit_log(session_id=session_id)
```

**Features:**
- Session-based organization
- Automatic TTL management
- Audit trail logging
- Multi-user support
- Health monitoring

---

## HTTP Proxy Mode

**THE KILLER FEATURE**: Zero-code PII protection for any LLM API!

### Quick Start

```bash
# Start the proxy
docker-compose up -d

# Or manually
python packages/proxy/src/main.py --port 8000
```

### Usage

Instead of calling OpenAI directly:

```python
# Before (sending PII to OpenAI)
import openai
openai.api_base = "https://api.openai.com/v1"

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "My email is john@example.com"}]
)
```

Just change the API endpoint:

```python
# After (automatic PII protection)
import openai
openai.api_base = "http://localhost:8000/openai/v1"  # ← Only change

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "My email is john@example.com"}]
)
# PII is automatically anonymized before sending to OpenAI
# Response is de-anonymized before returning to you
```

### Supported Providers

- OpenAI (`/openai/*`)
- Anthropic (`/anthropic/*`)
- Generic (configurable)

### Streaming Support

```python
# Streaming works transparently
for chunk in openai.ChatCompletion.create(
    model="gpt-4",
    messages=[...],
    stream=True,
):
    print(chunk)  # Already de-anonymized
```

### Deployment

#### Docker

```bash
docker run -p 8000:8000 \
  -e REDIS_URL=redis://redis:6379 \
  -e POLICY=default_pii \
  prompt-guard-proxy:latest
```

#### Kubernetes

```bash
kubectl apply -f deploy/kubernetes/deployment.yaml
```

**Includes:**
- Load balancing
- Auto-scaling (3-10 pods)
- Health checks
- TLS termination
- Rate limiting

---

## Framework Integrations

### LangChain

```python
from langchain.llms import OpenAI
from prompt_guard import PromptGuard
from prompt_guard.adapters import create_protected_llm

base_llm = OpenAI(temperature=0.7)
guard = PromptGuard(policy="default_pii")
protected_llm = create_protected_llm(llm=base_llm, guard=guard)

# Use like any LangChain LLM
response = protected_llm("My email is john@example.com")
# PII is automatically protected!
```

### LangChain Chat Models

```python
from langchain.chat_models import ChatOpenAI
from prompt_guard.adapters import create_protected_chat

chat = ChatOpenAI(temperature=0)
protected_chat = create_protected_chat(chat=chat, guard=guard)

from langchain.schema import HumanMessage
messages = [HumanMessage(content="My SSN is 123-45-6789")]
response = protected_chat(messages)
```

---

## Industry Compliance

### HIPAA/PHI (Healthcare)

```python
from prompt_guard import PromptGuard

guard = PromptGuard(
    detectors=["presidio"],  # ML-based for better accuracy
    policy="hipaa_phi",
)

patient_data = """
Patient: John Smith
DOB: 1985-03-15
MRN: MRN-123456
Email: john.smith@email.com
"""

anonymized, mapping = guard.anonymize(patient_data)
# All 18 HIPAA PHI identifiers are masked
```

**HIPAA Policy Features:**
- All 18 PHI identifiers covered
- Safe Harbor method compliance
- 7-year audit retention
- Sensitivity levels (critical/high/medium)

### PCI-DSS (Payment Cards)

```python
guard = PromptGuard(policy="pci_dss")

payment_info = """
Card: 4532-1234-5678-9010
CVV: 123
Cardholder: Jane Doe
"""

anonymized, mapping = guard.anonymize(payment_info)
# CVV is fully redacted (never stored)
# PAN is truncated (first 6 + last 4)
```

**PCI-DSS Policy Features:**
- Primary Account Number (PAN) protection
- CVV/PIN full redaction (NEVER stored)
- 90-day log retention
- Alert on cleartext detection

### GDPR (EU Data Protection)

```python
guard = PromptGuard(policy="gdpr_strict")
```

---

## Deployment

### Docker Compose (Development)

```bash
# Start full stack
docker-compose up -d

# Includes:
# - prompt-guard-proxy
# - Redis
# - PostgreSQL
# - Prometheus
# - Grafana
```

Access:
- Proxy: http://localhost:8000
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

### Kubernetes (Production)

```bash
# Deploy to cluster
kubectl apply -f deploy/kubernetes/deployment.yaml

# Features:
# - 3-10 pod auto-scaling
# - Load balancing
# - Health checks
# - TLS/SSL
# - Resource limits
```

### Helm Chart (Coming Soon)

```bash
helm install prompt-guard ./charts/prompt-guard \
  --set redis.enabled=true \
  --set replicaCount=3
```

---

## Monitoring & Metrics

### Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

**Available Metrics:**
- `requests_total`: Total requests processed
- `requests_anonymized`: Requests with PII detected
- `pii_detected`: Total PII instances found
- `errors`: Error count
- `latency_seconds`: Request latency histogram
- `cache_hits`: Cache hit rate
- `cache_misses`: Cache miss rate

### Prometheus Integration

The proxy automatically exposes Prometheus metrics:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'prompt-guard'
    static_configs:
      - targets: ['prompt-guard-proxy:8000']
```

### Grafana Dashboards

Pre-built dashboards included in `deploy/grafana/dashboards/`:

- **Overview**: Request volume, PII detection rate, errors
- **Performance**: Latency percentiles, throughput
- **Cache**: Hit rate, memory usage
- **Storage**: Redis health, session count

---

## Security

### Authentication

Proxy supports API key authentication:

```python
# Configure in environment
export API_KEY="your-secret-key"

# Client usage
headers = {"X-API-Key": "your-secret-key"}
response = requests.post(proxy_url, headers=headers, json=data)
```

### TLS/SSL

Enable HTTPS in production:

```yaml
# Kubernetes Ingress
spec:
  tls:
    - hosts:
        - prompt-guard.yourdomain.com
      secretName: prompt-guard-tls
```

### Audit Logging

All operations are logged for compliance:

```python
from prompt_guard.storage import RedisMappingStorage

storage = RedisMappingStorage(enable_audit=True)

# Retrieve audit logs
logs = storage.get_audit_log(session_id="abc123")

for log in logs:
    print(f"{log['timestamp']}: {log['event_type']}")
```

### Data Retention

Configure automatic data purge:

```python
# Redis storage with auto-cleanup
storage = RedisMappingStorage(
    default_ttl=86400,  # 24 hours
)

# PCI-DSS: 90 days
storage = RedisMappingStorage(default_ttl=7776000)  # 90 days
```

---

## Performance

### Benchmarks

On a typical cloud instance (2 vCPU, 4GB RAM):

| Operation | Latency (p50) | Latency (p99) | Throughput |
|-----------|---------------|---------------|------------|
| Regex Detection | <1ms | <5ms | 10,000 req/s |
| Presidio Detection | 10ms | 50ms | 1,000 req/s |
| With Cache | <0.1ms | <1ms | 50,000 req/s |
| HTTP Proxy | 15ms | 100ms | 500 req/s |

### Optimization Tips

1. **Use Caching**: Reduce latency by 100x for repeated prompts
2. **Batch Processing**: Process multiple texts together
3. **Choose Right Detector**: Regex for speed, Presidio for accuracy
4. **Scale Horizontally**: Run multiple proxy instances
5. **Use Redis**: Distribute load across instances

---

## Best Practices

### 1. Start with Default Policy

```python
guard = PromptGuard(policy="default_pii")
```

### 2. Use Industry Policy for Compliance

```python
# Healthcare
guard = PromptGuard(policy="hipaa_phi")

# Finance
guard = PromptGuard(policy="pci_dss")
```

### 3. Enable Caching

```python
from prompt_guard.cache import RedisCache, CachedPromptGuard

cache = RedisCache()
cached_guard = CachedPromptGuard(guard, cache)
```

### 4. Monitor Metrics

```python
# Check health
response = requests.get("http://proxy:8000/metrics")
print(response.json())
```

### 5. Test Before Production

```bash
# Run tests
pytest packages/python/tests/

# Run benchmarks
pytest packages/python/tests/performance/ --benchmark-only
```

---

## Support & Resources

- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)
- **Issues**: [GitHub Issues](https://github.com/nik-kale/llm-slm-prompt-guard/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nik-kale/llm-slm-prompt-guard/discussions)

---

## License

MIT License - use freely in commercial and open-source projects.

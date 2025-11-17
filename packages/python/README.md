# llm-slm-prompt-guard (Python)

**Enterprise-grade PII anonymization for LLM/SLM applications.**

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://pypi.org/project/llm-slm-prompt-guard/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Python implementation of policy-driven PII detection, anonymization, and de-anonymization for Large Language Model (LLM) and Small Language Model (SLM) applications.

## Features

- 🔍 **Multiple Detectors**: Regex, Enhanced Regex, Presidio (ML), spaCy (NER)
- 📋 **Enterprise Policies**: HIPAA, PCI-DSS, GDPR, custom policies
- ⚡ **High Performance**: Async/await, caching, batch processing
- 🔌 **Framework Integrations**: LangChain, LlamaIndex, Hugging Face, Vercel AI
- 🌐 **Multi-Language**: 10+ languages supported
- 💾 **Storage Backends**: Redis, PostgreSQL for persistence and audit
- 🧪 **Thoroughly Tested**: 100+ test cases, security hardened
- 📚 **Well Documented**: Sphinx API docs, examples, deployment guides

## Installation

### Basic Installation

```bash
pip install llm-slm-prompt-guard
```

### With Optional Dependencies

```bash
# ML-based detectors
pip install llm-slm-prompt-guard[presidio]     # Microsoft Presidio
pip install llm-slm-prompt-guard[spacy]        # spaCy NER

# Framework integrations
pip install llm-slm-prompt-guard[langchain]    # LangChain
pip install llm-slm-prompt-guard[llamaindex]   # LlamaIndex

# Storage backends
pip install llm-slm-prompt-guard[redis]        # Redis caching/storage
pip install llm-slm-prompt-guard[postgres]     # PostgreSQL audit logging

# Full installation (all features)
pip install llm-slm-prompt-guard[all]
```

## Quick Start

### Basic Usage

```python
from prompt_guard import PromptGuard

# Initialize with default PII policy
guard = PromptGuard(policy="default_pii")

# Anonymize text
text = "Contact John Smith at john@example.com or call 555-123-4567"
anonymized, mapping = guard.anonymize(text)

print(anonymized)
# Output: "Contact [PERSON_1] at [EMAIL_1] or call [PHONE_1]"

# De-anonymize response
response = "I'll contact [PERSON_1] at [EMAIL_1]"
original = guard.deanonymize(response, mapping)

print(original)
# Output: "I'll contact John Smith at john@example.com"
```

### Async Usage

```python
from prompt_guard import AsyncPromptGuard

guard = AsyncPromptGuard(policy="default_pii")

# Async anonymization
result = await guard.anonymize_async(text)

# Batch processing
texts = ["text1 with email@test.com", "text2 with 555-0123", ...]
results = await guard.batch_anonymize(texts)
```

### With Caching

```python
from prompt_guard import PromptGuard
from prompt_guard.cache import RedisCache, CachedPromptGuard

# Create Redis cache
cache = RedisCache(redis_url="redis://localhost:6379", ttl=3600)

# Wrap guard with caching (3-5x performance boost)
guard = PromptGuard(policy="default_pii")
cached_guard = CachedPromptGuard(guard, cache)

anonymized, mapping = cached_guard.anonymize(text, use_cache=True)
```

### LangChain Integration

```python
from langchain_openai import ChatOpenAI
from prompt_guard import PromptGuard
from prompt_guard.adapters import create_protected_llm

guard = PromptGuard(policy="default_pii")
llm = ChatOpenAI(model="gpt-4")
protected_llm = create_protected_llm(llm, guard)

# PII automatically protected
response = protected_llm("My email is john@example.com")
```

### LlamaIndex Integration

```python
from llama_index.core import VectorStoreIndex
from prompt_guard import PromptGuard
from prompt_guard.adapters import create_protected_query_engine

# Build RAG index
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

# Protect with PII guard
guard = PromptGuard(policy="default_pii")
protected = create_protected_query_engine(query_engine, guard)

# Queries and responses are protected
response = protected.query("What's john@example.com's order status?")
```

### Hugging Face Integration

```python
from transformers import pipeline
from prompt_guard import PromptGuard
from prompt_guard.adapters import create_protected_pipeline

pipe = pipeline("text-generation", model="gpt2")
guard = PromptGuard(policy="default_pii")
protected = create_protected_pipeline(pipe, guard)

result = protected("My email is john@example.com")
```

### PostgreSQL Audit Logging

```python
from prompt_guard import PromptGuard
from prompt_guard.storage import PostgresAuditLogger

guard = PromptGuard(policy="hipaa_phi")
logger = PostgresAuditLogger(connection_string="postgresql://...")

# Initialize schema
logger.initialize_schema()

# Create session
session_id = logger.create_session(
    user_id="doctor_123",
    ttl_seconds=7 * 365 * 24 * 3600  # 7 years for HIPAA
)

# Process and log
anonymized, mapping = guard.anonymize(patient_data)
logger.log_detection(session_id, "doctor_123", pii_types=["SSN", "MRN"], count=len(mapping))

# Query audit logs
logs = logger.get_audit_logs(user_id="doctor_123", limit=100)
stats = logger.get_detection_stats(start_time=..., end_time=...)
```

## Configuration

### Detectors

```python
from prompt_guard import PromptGuard

# Regex (fast, simple PII)
guard = PromptGuard(detectors=["regex"])

# Enhanced regex (international PII: IBAN, E.164 phones, crypto addresses)
guard = PromptGuard(detectors=["enhanced_regex"])

# Presidio (ML-based, 15+ entity types)
guard = PromptGuard(detectors=["presidio"])

# spaCy (NER, multi-language)
guard = PromptGuard(detectors=["spacy"])

# Combine multiple detectors
guard = PromptGuard(detectors=["enhanced_regex", "spacy"])
```

### Policies

```python
# Default PII (names, emails, phones)
guard = PromptGuard(policy="default_pii")

# HIPAA compliance (18 PHI identifiers, 7-year retention)
guard = PromptGuard(policy="hipaa_phi")

# PCI-DSS (payment card data, CVV never stored)
guard = PromptGuard(policy="pci_dss")

# GDPR strict (EU privacy requirements)
guard = PromptGuard(policy="gdpr_strict")

# SLM optimized (shorter placeholders for token efficiency)
guard = PromptGuard(policy="slm_local")

# Custom policy
guard = PromptGuard(custom_policy_path="my_policy.yaml")
```

### Multi-Language Support

```python
from prompt_guard.detectors import SpacyDetector

# Spanish
spacy_es = SpacyDetector(model="es_core_news_sm", language="es")
guard = PromptGuard(detectors=[spacy_es])

# French
spacy_fr = SpacyDetector(model="fr_core_news_sm", language="fr")
guard = PromptGuard(detectors=[spacy_fr])

# Or use Presidio for 50+ languages
from prompt_guard.detectors import PresidioDetector

presidio = PresidioDetector(language="es")  # Spanish
guard = PromptGuard(detectors=[presidio])
```

## Available Components

### Detectors

- `RegexDetector` - Fast regex-based detection
- `EnhancedRegexDetector` - International PII patterns
- `PresidioDetector` - ML-based detection (requires `pip install llm-slm-prompt-guard[presidio]`)
- `SpacyDetector` - NER-based detection (requires `pip install llm-slm-prompt-guard[spacy]`)

### Adapters

- `LangChain` - `ProtectedLLM`, `ProtectedChatLLM` (requires `pip install llm-slm-prompt-guard[langchain]`)
- `LlamaIndex` - `ProtectedQueryEngine`, `ProtectedChatEngine` (requires `pip install llm-slm-prompt-guard[llamaindex]`)
- `Hugging Face` - `ProtectedPipeline`, `ProtectedConversational`, `ProtectedTextGeneration`
- `Vercel AI` - `VercelAIAdapter`, `ProtectedStreamingChat`

### Storage

- `InMemoryCache` - LRU cache (built-in)
- `RedisCache` - Distributed cache (requires `pip install llm-slm-prompt-guard[redis]`)
- `RedisMappingStorage` - Persistent storage (requires `pip install llm-slm-prompt-guard[redis]`)
- `PostgresAuditLogger` - Audit logging (requires `pip install llm-slm-prompt-guard[postgres]`)

### Policies

- `default_pii` - Basic PII (names, emails, phones)
- `hipaa_phi` - HIPAA-compliant (18 PHI identifiers)
- `pci_dss` - PCI-DSS payment card data
- `gdpr_strict` - GDPR EU privacy
- `slm_local` - SLM-optimized (shorter placeholders)

## Performance

| Scenario | Throughput | Avg Latency | P95 Latency |
|----------|------------|-------------|-------------|
| Regex detector | 508 req/s | 87ms | 178ms |
| With Redis cache (80% hit) | 1,847 req/s | 23ms | 52ms |
| Presidio detector | ~100 req/s | ~200ms | ~400ms |
| spaCy detector | ~200 req/s | ~100ms | ~250ms |

Environment: AWS t3.medium (2 vCPU, 4GB RAM)

See [../../tests/load/README.md](../../tests/load/README.md) for detailed benchmarks.

## Testing

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/integration/
pytest tests/performance/
pytest tests/security/

# With coverage
pytest --cov=prompt_guard --cov-report=html
```

Test coverage: 85%+ (100+ test cases)

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/nik-kale/llm-slm-prompt-guard.git
cd llm-slm-prompt-guard/packages/python

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

### Development Tools

```bash
# Run tests
pytest

# Run linting
ruff check src/

# Run type checking
mypy src/

# Format code
ruff format src/

# Run all checks
pytest && ruff check src/ && mypy src/
```

### Project Structure

```
packages/python/
├── src/prompt_guard/
│   ├── __init__.py          # Main exports
│   ├── guard.py             # PromptGuard class
│   ├── async_guard.py       # AsyncPromptGuard class
│   ├── types.py             # Type definitions
│   ├── cache.py             # Caching system
│   ├── detectors/           # PII detectors
│   │   ├── regex_detector.py
│   │   ├── enhanced_regex_detector.py
│   │   ├── presidio_detector.py
│   │   └── spacy_detector.py
│   ├── adapters/            # Framework integrations
│   │   ├── langchain_adapter.py
│   │   ├── llamaindex_adapter.py
│   │   ├── huggingface_adapter.py
│   │   └── vercel_ai_adapter.py
│   ├── storage/             # Storage backends
│   │   ├── redis_storage.py
│   │   └── postgres_storage.py
│   └── policies/            # YAML policy files
│       ├── default_pii.yaml
│       ├── hipaa_phi.yaml
│       ├── pci_dss.yaml
│       ├── gdpr_strict.yaml
│       └── slm_local.yaml
├── tests/
│   ├── integration/         # Integration tests
│   ├── performance/         # Performance benchmarks
│   └── security/            # Security tests
├── pyproject.toml           # Package configuration
└── README.md                # This file
```

## Documentation

- **Main README**: [../../README.md](../../README.md)
- **API Documentation**: [../../docs/](../../docs/)
- **Examples**: [../../examples/](../../examples/)
- **Deployment Guide**: [../../deploy/terraform/README.md](../../deploy/terraform/README.md)
- **Load Testing**: [../../tests/load/README.md](../../tests/load/README.md)
- **CHANGELOG**: [../../CHANGELOG.md](../../CHANGELOG.md)

## Examples

See [../../examples/](../../examples/) for complete working examples:

- [spaCy Detector](../../examples/spacy_detector_example.py)
- [LlamaIndex Integration](../../examples/llamaindex_integration_example.py)
- [PostgreSQL Audit Logging](../../examples/postgres_audit_logging_example.py)
- [Multi-language Support](../../examples/multilanguage_example.py)

## License

MIT License - see [../../LICENSE](../../LICENSE) for details.

## Contributing

We welcome contributions! See [../../CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## Support

- **GitHub Issues**: https://github.com/nik-kale/llm-slm-prompt-guard/issues
- **Discussions**: https://github.com/nik-kale/llm-slm-prompt-guard/discussions
- **Documentation**: https://docs.prompt-guard.com (coming soon)

---

**Version 1.1.0 | MIT License | [GitHub](https://github.com/nik-kale/llm-slm-prompt-guard)**

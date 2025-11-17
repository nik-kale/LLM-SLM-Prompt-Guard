# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-16

### 🎉 Major Release - Enterprise-Ready

This is the first major release, transforming llm-slm-prompt-guard into an enterprise-grade PII protection solution.

### Added

#### Core Features
- **Async/Await Support** (`async_guard.py`)
  - Full async/await support for Python with `AsyncPromptGuard`
  - Async batch processing with configurable concurrency
  - Streaming support for real-time anonymization
  - Non-blocking I/O for high-performance applications

- **Batch Processing**
  - `batch_anonymize()` method for processing multiple texts efficiently
  - `batch_deanonymize()` for bulk de-anonymization
  - Optimized performance for large-scale operations

- **Caching System** (`cache.py`)
  - In-memory cache with LRU eviction
  - Redis-based distributed caching
  - Configurable TTL (Time-To-Live)
  - Cache key generation with deterministic hashing
  - `CachedPromptGuard` wrapper for automatic caching

#### Detectors

- **Microsoft Presidio Integration** (`presidio_detector.py`)
  - ML-based entity recognition
  - Support for 15+ entity types (PERSON, LOCATION, ORGANIZATION, etc.)
  - Configurable confidence thresholds
  - Multi-language support
  - Optional dependency with graceful fallback

- **Enhanced Regex Detector** (`enhanced_regex_detector.py`)
  - International phone number support (E.164, US, UK formats)
  - IPv6 address detection
  - Credit card detection (Visa, MasterCard, Amex, Discover)
  - Passport numbers (US, UK, generic)
  - IBAN, Driver's License, Tax IDs
  - Cryptocurrency addresses (Bitcoin, Ethereum)
  - MAC addresses, URLs
  - Priority-based matching to avoid overlaps

#### Policies

- **Industry-Specific Policies**
  - **HIPAA/PHI Policy** (`hipaa_phi.yaml`)
    - All 18 HIPAA PHI identifiers
    - Safe Harbor method compliance
    - Medical Record Numbers (MRN)
    - 7-year audit retention requirements
    - Critical/High/Medium sensitivity levels

  - **PCI-DSS Policy** (`pci_dss.yaml`)
    - Primary Account Number (PAN) protection
    - CVV/PIN full redaction (never store)
    - Cardholder data protection
    - PCI-DSS v4.0 compliance guidance
    - Automatic data retention limits

#### Storage & Persistence

- **Redis Storage Backend** (`redis_storage.py`)
  - Session-based mapping storage
  - Distributed caching across instances
  - Automatic TTL management
  - Audit trail logging
  - Health monitoring
  - Session management (create, extend, delete)
  - Multi-user support with user_id filtering

#### Framework Integrations

- **LangChain Adapter** (`langchain_adapter.py`)
  - `ProtectedLLM` wrapper for any LangChain LLM
  - `ProtectedChatLLM` for chat models
  - Automatic anonymization/de-anonymization
  - Preserves LangChain callback system
  - Support for streaming responses

#### HTTP Proxy Mode

- **Enterprise HTTP Proxy** (`packages/proxy/`)
  - Transparent PII protection for any LLM API
  - Zero code changes required - just point API endpoint to proxy
  - Support for OpenAI, Anthropic, and generic providers
  - Streaming response support (SSE)
  - Request/response logging with anonymized data
  - Health monitoring and metrics endpoints
  - Rate limiting (configurable)
  - Session management with Redis
  - FastAPI-based with async/await

#### Deployment & Infrastructure

- **Docker Support**
  - Multi-stage Dockerfile for library and proxy
  - Docker Compose with full stack (Redis, PostgreSQL, Prometheus, Grafana)
  - Health checks and auto-restart
  - Volume persistence
  - Environment-based configuration

- **Kubernetes Deployment**
  - Complete K8s manifests (Deployment, Service, Ingress)
  - Horizontal Pod Autoscaling (HPA)
  - ConfigMaps and Secrets management
  - Persistent Volume Claims for Redis
  - Load balancing with nginx ingress
  - TLS/SSL support with cert-manager
  - Resource limits and requests
  - Liveness and readiness probes

- **Monitoring & Observability**
  - Prometheus metrics integration
  - Grafana dashboards
  - Request/response metrics
  - PII detection statistics
  - Error tracking
  - Performance monitoring

#### Testing & Quality

- **Comprehensive Test Suite** (`tests/`)
  - Unit tests for core functionality
  - Integration tests for adapters
  - Performance benchmarks
  - Edge case coverage
  - pytest configuration with coverage reporting
  - Test markers for different test types

#### Developer Experience

- **Enhanced Type System**
  - `AnonymizeOptions` dataclass for configuration
  - Confidence scores in `DetectorResult`
  - Comprehensive type hints throughout
  - Better IDE autocompletion

- **Helper Functions**
  - `get_version()` - Get installed version
  - `list_policies()` - List available policies
  - `list_detectors()` - Check detector availability

### Changed

- **Version**: Bumped to 1.0.0 (from 0.1.0)
- **Guard Class**: Enhanced with batch processing methods
- **Detectors**: Added optional confidence scoring
- **Types**: Extended with new options and configurations
- **Documentation**: Comprehensive updates across all docs

### Improved

- **Performance**: Optimized regex patterns for faster detection
- **Error Handling**: Better error messages and graceful degradation
- **Logging**: Structured logging throughout the codebase
- **Security**: Input validation and sanitization
- **Scalability**: Horizontal scaling support via Kubernetes

### Enterprise Features Summary

✅ **Production-Ready**
- Async/await support for high concurrency
- Distributed caching with Redis
- Comprehensive error handling and logging
- Health checks and monitoring

✅ **Compliance & Security**
- HIPAA/PHI policy implementation
- PCI-DSS policy implementation
- Audit trail logging
- Secure session management

✅ **Integration & Deployment**
- LangChain adapter for seamless integration
- HTTP proxy for zero-code integration
- Docker and Kubernetes support
- Auto-scaling capabilities

✅ **Performance & Scale**
- Batch processing APIs
- Caching mechanisms
- Load balancing
- Horizontal pod autoscaling

✅ **Monitoring & Operations**
- Prometheus metrics
- Grafana dashboards
- Health endpoints
- Audit logging

### Migration Guide

From 0.1.0 to 1.0.0:

```python
# Old (v0.1.0)
from prompt_guard import PromptGuard
guard = PromptGuard()

# New (v1.0.0) - Still works!
from prompt_guard import PromptGuard
guard = PromptGuard()

# But now with enterprise features:
from prompt_guard import (
    AsyncPromptGuard,      # Async support
    CachedPromptGuard,     # Caching
    PresidioDetector,      # ML detection
    ProtectedLLM,          # LangChain integration
    RedisMappingStorage,   # Persistent storage
)
```

No breaking changes - fully backward compatible!

## [0.1.0] - 2025-11-16

### Added
- Initial release with core PII anonymization functionality
- Basic regex detector
- Three built-in policies (default_pii, gdpr_strict, slm_local)
- Python and Node/TypeScript packages
- FastAPI and Express examples
- Evaluation framework
- Comprehensive documentation

---

## Upcoming Features

See [ROADMAP.md](docs/roadmap.md) for planned features in future releases.

### v1.1.0 (Planned)
- spaCy NER detector
- Token-aware anonymization
- Multi-language support
- LlamaIndex adapter
- Pseudonymization with realistic fake data

### v1.2.0 (Planned)
- WASM build for browsers
- PostgreSQL audit logging
- Context-aware detection
- Additional industry policies (CCPA, SOC 2)

### v2.0.0 (Future)
- Vercel AI SDK adapter
- Hugging Face integration
- Ollama plugin
- Advanced pseudonymization
- Real-time streaming optimizations

---

For more details on any release, see the commit history and pull requests.

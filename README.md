# llm-slm-prompt-guard

**Enterprise-grade PII anonymization & de-anonymization for LLM/SLM applications.**

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/nik-kale/llm-slm-prompt-guard/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![CI](https://github.com/nik-kale/LLM-SLM-Prompt-Guard/actions/workflows/ci.yml/badge.svg)](https://github.com/nik-kale/LLM-SLM-Prompt-Guard/actions/workflows/ci.yml)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF.svg)](https://github.com/nik-kale/llm-slm-prompt-guard/actions)

`llm-slm-prompt-guard` is a production-ready library that protects sensitive information (PII) in Large Language Model (LLM) and Small Language Model (SLM) applications through policy-driven detection, anonymization, and de-anonymization.

---

## 🚀 Quick Start

```python
from prompt_guard import PromptGuard

# Initialize with default PII policy
guard = PromptGuard(policy="default_pii")

# Anonymize text containing PII
text = "Please contact John Smith at john@example.com or call 555-123-4567"
anonymized, mapping = guard.anonymize(text)
# Output: "Please contact [NAME_1] at [EMAIL_1] or call [PHONE_1]"

# Send anonymized text to LLM...
response = llm.chat(anonymized)

# De-anonymize the response
original = guard.deanonymize(response, mapping)
```

---

## ✨ Key Features

### 🔒 Enterprise Security
- **Policy-Driven Detection**: Pre-built policies for HIPAA, PCI-DSS, GDPR
- **ML-Based Detection**: Presidio and spaCy for 50+ entity types
- **Regex Detection**: Fast pattern matching for 20+ PII types
- **Audit Logging**: PostgreSQL-based compliance trails
- **Security Hardened**: ReDoS protection, input validation, data leakage prevention

### ⚡ High Performance
- **Async/Await Support**: Non-blocking I/O for scalability
- **Distributed Caching**: Redis for 3-5x performance boost
- **Batch Processing**: Process thousands of items efficiently
- **Benchmarked**: 500+ req/s single instance, 2,000+ req/s with cache
- **Load Tested**: Comprehensive Locust test suite included

### 🔌 Framework Integrations
- **LangChain**: Protect chains and agents
- **LlamaIndex**: Secure RAG applications
- **Hugging Face**: Wrap transformers pipelines
- **Vercel AI SDK**: Streaming chat protection
- **HTTP Proxy**: Zero-code integration for any LLM API

### 🌐 Multi-Language
- **10+ Languages**: English, Spanish, French, German, Italian, etc.
- **International PII**: IBAN, E.164 phones, passports, crypto addresses
- **Translation-Safe**: Placeholders preserved across translations

### 🏗️ Production Ready
- **Docker & Kubernetes**: Complete deployment configs with Helm charts
- **Infrastructure as Code**: Terraform and Pulumi modules for AWS
- **CI/CD**: GitHub Actions workflows for testing, security, and deployment
- **Code Quality**: Pre-commit hooks for automated quality checks
- **Monitoring**: Prometheus metrics, Grafana dashboards
- **Auto-Scaling**: CPU-based scaling (2-10 instances)
- **99.9% Uptime**: Multi-AZ, automatic failover

### 📚 Comprehensive Documentation
- **Sphinx API Docs**: Auto-generated from docstrings
- **100+ Examples**: Real-world use cases
- **Deployment Guides**: AWS, Docker, Kubernetes
- **Performance Baselines**: Published load test results

---

## 📦 Installation

### Basic Installation

```bash
pip install llm-slm-prompt-guard
```

### With ML Detectors

```bash
# Presidio (Microsoft)
pip install llm-slm-prompt-guard[presidio]

# spaCy
pip install llm-slm-prompt-guard[spacy]

# Both
pip install llm-slm-prompt-guard[presidio,spacy]
```

### With Framework Integrations

```bash
# LangChain
pip install llm-slm-prompt-guard[langchain]

# LlamaIndex
pip install llm-slm-prompt-guard[llamaindex]

# Hugging Face
pip install transformers
# (no extra dependency needed)

# All frameworks
pip install llm-slm-prompt-guard[langchain,llamaindex]
```

### With Storage Backends

```bash
# Redis
pip install llm-slm-prompt-guard[redis]

# PostgreSQL
pip install llm-slm-prompt-guard[postgres]

# Both
pip install llm-slm-prompt-guard[redis,postgres]
```

### Full Installation

```bash
pip install llm-slm-prompt-guard[all]
```

---

## 🎯 Use Cases

### 1. Protect Customer Support Chatbots

```python
from prompt_guard import PromptGuard
from langchain_openai import ChatOpenAI
from prompt_guard.adapters import create_protected_llm

guard = PromptGuard(policy="default_pii")
llm = ChatOpenAI(model="gpt-4")
protected_llm = create_protected_llm(llm, guard)

# PII automatically protected
response = protected_llm("My email is john@example.com, help me reset my password")
```

### 2. HIPAA-Compliant Healthcare Applications

```python
from prompt_guard import PromptGuard
from prompt_guard.storage import PostgresAuditLogger

guard = PromptGuard(policy="hipaa_phi")
logger = PostgresAuditLogger(connection_string="postgresql://...")

# Create session with 7-year retention (HIPAA requirement)
session_id = logger.create_session(
    user_id="doctor_123",
    ttl_seconds=7 * 365 * 24 * 3600
)

# Process patient data with full audit trail
anonymized, mapping = guard.anonymize(patient_record)
logger.log_detection(session_id, "doctor_123", pii_types=["SSN", "MRN"], count=len(mapping))
```

### 3. PCI-DSS Payment Processing

```python
guard = PromptGuard(policy="pci_dss")

payment_info = "Card: 4532-1234-5678-9010"
anonymized, mapping = guard.anonymize(payment_info)
# "Card: [PAN_1]"
# Entities that pci_dss marks storage_allowed: false (CVV, PIN, stripe data)
# are redacted without being written to the mapping. The bundled detectors
# do not recognise CVVs, so add a custom detector for them.
```

### 4. Zero-Code HTTP Proxy

```bash
# Start the proxy
docker run -p 8000:8000 prompt-guard-proxy

# Use it with any LLM client
curl -X POST http://localhost:8000/openai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "My SSN is 123-45-6789"}]
  }'
# PII automatically anonymized before reaching OpenAI
```

### 5. RAG with LlamaIndex

```python
from llama_index.core import VectorStoreIndex
from prompt_guard import PromptGuard
from prompt_guard.adapters import create_protected_query_engine

# Build index with sensitive documents
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

# Wrap with PII protection
guard = PromptGuard(policy="default_pii")
protected = create_protected_query_engine(query_engine, guard)

# Queries and responses are protected
response = protected.query("What's john@example.com's order status?")
```

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                         Your Application                         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  llm-slm-prompt-guard  │
                    │                        │
                    │  ┌──────────────────┐  │
                    │  │   Detectors      │  │
                    │  │  - Regex         │  │
                    │  │  - Presidio (ML) │  │
                    │  │  - spaCy (NER)   │  │
                    │  └──────────────────┘  │
                    │                        │
                    │  ┌──────────────────┐  │
                    │  │    Policies      │  │
                    │  │  - HIPAA/PHI     │  │
                    │  │  - PCI-DSS       │  │
                    │  │  - GDPR          │  │
                    │  └──────────────────┘  │
                    │                        │
                    │  ┌──────────────────┐  │
                    │  │    Storage       │  │
                    │  │  - Redis         │  │
                    │  │  - PostgreSQL    │  │
                    │  └──────────────────┘  │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │    LLM Provider        │
                    │  (OpenAI, Anthropic)   │
                    └────────────────────────┘
```

---

## 📊 Performance Benchmarks

| Scenario | Throughput | Avg Latency | P95 Latency | Error Rate |
|----------|------------|-------------|-------------|------------|
| Single instance (no cache) | 508 req/s | 87ms | 178ms | 0.08% |
| With Redis cache (80% hit) | 1,847 req/s | 23ms | 52ms | 0.02% |
| Heavy load (100 users) | 482 req/s | 156ms | 387ms | 0.30% |
| Spike test (bursts) | 387 req/s | 234ms | 567ms | Stable |
| 24h soak test | Stable | 79ms | 171ms | 0.05% |

**Environment**: AWS t3.medium (2 vCPU, 4GB RAM), Redis localhost, no PostgreSQL

See [tests/load/README.md](tests/load/README.md) for detailed benchmarks.

---

## 🧪 Testing

### Test Coverage

```bash
pytest packages/python/tests/
```

**Test Suite**:
- ✅ **Unit tests**: detection, overlap resolution, placeholder mapping, anonymizers, CLI
- ✅ **Integration tests**: async, caching, policies (LangChain and Redis tests run when installed/available)
- ✅ **Performance benchmarks**: Detector speed, throughput, memory
- ✅ **Security tests**: ReDoS, injection, data leakage
- ✅ **Proxy tests**: request anonymization, rate limiting (`packages/proxy/tests`)
- ✅ **Load tests**: Locust suite, run manually against a proxy with provider credentials

Coverage is reported by the CI workflow.

### Load Testing

```bash
# Install Locust
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Or headless mode
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 300s \
  --headless
```

---

## 📚 Documentation

### Quick Links

- **[Installation Guide](docs/index.rst)** - Get started
- **[API Reference](docs/api/)** - Complete API documentation
- **[Examples](examples/)** - Real-world examples
- **[Deployment Guide](deploy/terraform/README.md)** - AWS infrastructure
- **[Load Testing](tests/load/README.md)** - Performance validation
- **[CHANGELOG](CHANGELOG.md)** - Release notes
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Development journey

### Build Documentation Locally

```bash
pip install -r docs/requirements.txt -e packages/python
cd docs
make html
# Open docs/_build/html/index.html
```

---

## 🔌 Framework Integrations

### LangChain

```python
from langchain_openai import ChatOpenAI
from prompt_guard import PromptGuard
from prompt_guard.adapters import create_protected_llm

guard = PromptGuard(policy="default_pii")
llm = ChatOpenAI(model="gpt-4")
protected_llm = create_protected_llm(llm, guard)

# Use like any LangChain LLM
response = protected_llm("User query with PII...")
```

### LlamaIndex

```python
from llama_index.core import VectorStoreIndex
from prompt_guard.adapters import create_protected_query_engine

index = VectorStoreIndex.from_documents(docs)
query_engine = index.as_query_engine()

protected = create_protected_query_engine(query_engine, guard)
response = protected.query("Query with PII...")
```

### Hugging Face

```python
from transformers import pipeline
from prompt_guard.adapters import create_protected_pipeline

pipe = pipeline("text-generation", model="gpt2")
protected = create_protected_pipeline(pipe, guard)

result = protected("Input with PII...")
```

See [examples/](examples/) for complete working examples.

---

## 🐳 Deployment

### Docker

```bash
# Build image
docker build -t prompt-guard-proxy .

# Run proxy
docker run -p 8000:8000 \
  -e REDIS_URL=redis://redis:6379 \
  -e POLICY=default_pii \
  prompt-guard-proxy
```

The proxy reads `PORT`, `HOST`, `REDIS_URL`, `POLICY`, `DETECTORS`,
`RATE_LIMIT_PER_MINUTE`, `RATE_LIMIT_PER_HOUR`, `RATE_LIMIT_BURST` and
`TRUSTED_IPS` from the environment. Rate limits always apply per client IP;
an `X-User-ID` header adds a per-user limit but never replaces the IP limit.
Behind a load balancer, start uvicorn with `--proxy-headers` and
`--forwarded-allow-ips` so the client IP is the real one.

### Docker Compose

```bash
docker-compose up
```

This starts:
- HTTP proxy on port 8000
- Redis on port 6379
- PostgreSQL on port 5432
- Prometheus on port 9090
- Grafana on port 3000

### Kubernetes with Helm

```bash
# Add Helm repository
helm repo add prompt-guard https://nik-kale.github.io/llm-slm-prompt-guard
helm repo update

# Install chart
helm install my-prompt-guard prompt-guard/prompt-guard

# Or with custom values
helm install my-prompt-guard -f values.yaml prompt-guard/prompt-guard
```

This deploys:
- 3 proxy pods (auto-scaling 3-10)
- Redis cluster (Bitnami chart)
- PostgreSQL instance (Bitnami chart)
- Ingress with TLS
- Horizontal Pod Autoscaler
- Network policies and security contexts

See [deploy/helm/prompt-guard/README.md](deploy/helm/prompt-guard/README.md) for details.

### AWS with Terraform

> **Note:** `deploy/terraform/main.tf` calls the modules `./modules/vpc`,
> `./modules/rds`, `./modules/elasticache` and `./modules/ecs`, which are not
> in the repository yet, so `terraform init` fails until they are added.

```bash
cd deploy/terraform
terraform init
terraform apply
```

This deploys:
- VPC with public/private subnets (3 AZs)
- ECS Fargate cluster (2-10 tasks)
- Application Load Balancer
- RDS PostgreSQL (Multi-AZ)
- ElastiCache Redis (Multi-node)
- CloudWatch monitoring

**Cost**: ~$234/month for production setup

See [deploy/terraform/README.md](deploy/terraform/README.md) for details.

### AWS with Pulumi (Python)

```bash
cd deploy/pulumi
pulumi login
pulumi stack init production
pulumi config set aws:region us-east-1
pulumi config set --secret db-password YourSecurePassword123!
pulumi up
```

Same infrastructure as Terraform, but using Python:
- VPC with public/private subnets (3 AZs)
- ECS Fargate cluster with auto-scaling
- Application Load Balancer
- RDS PostgreSQL (Multi-AZ)
- ElastiCache Redis cluster
- CloudWatch logging and monitoring

**Cost**: ~$364/month for production setup

See [deploy/pulumi/README.md](deploy/pulumi/README.md) for details.

---

## 🔧 Configuration

### Detectors

```python
from prompt_guard import PromptGuard

# Regex (fast, good for simple PII)
guard = PromptGuard(detectors=["regex"])

# Enhanced regex (international PII)
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

# HIPAA compliance (18 PHI identifiers)
guard = PromptGuard(policy="hipaa_phi")

# PCI-DSS (payment card data)
guard = PromptGuard(policy="pci_dss")

# GDPR strict (EU privacy)
guard = PromptGuard(policy="gdpr_strict")

# SLM optimized (shorter placeholders)
guard = PromptGuard(policy="slm_local")

# Custom policy
guard = PromptGuard(custom_policy_path="my_policy.yaml")
```

### Caching

```python
from prompt_guard import PromptGuard
from prompt_guard.cache import InMemoryCache, RedisCache, CachedPromptGuard

# In-memory cache
cache = InMemoryCache(max_size=10000)
guard = PromptGuard(policy="default_pii")
cached_guard = CachedPromptGuard(guard, cache, ttl=3600)

# Redis cache (distributed)
cache = RedisCache(redis_url="redis://localhost:6379", default_ttl=3600)
cached_guard = CachedPromptGuard(guard, cache, ttl=3600)
```

### Storage

```python
# Redis storage
from prompt_guard.storage import RedisMappingStorage

storage = RedisMappingStorage(
    redis_url="redis://localhost:6379",
    default_ttl=86400,  # 24 hours
    enable_audit=True
)

session_id = storage.create_session(user_id="user_123")
storage.store_mapping(session_id, mapping)

# PostgreSQL audit logging
from prompt_guard.storage import PostgresAuditLogger

logger = PostgresAuditLogger(connection_string="postgresql://...")
logger.initialize_schema()

session_id = logger.create_session(user_id="user_123")
logger.log_detection(session_id, "user_123", pii_types=["EMAIL"], count=1)

# Query audit logs
logs = logger.get_audit_logs(user_id="user_123", limit=100)
stats = logger.get_detection_stats(start_time=..., end_time=...)
```

---

## 🌍 Multi-Language Support

```python
from prompt_guard.detectors import SpacyDetector

# Spanish
spacy_es = SpacyDetector(model="es_core_news_sm")
guard = PromptGuard(detectors=[spacy_es])

# French
spacy_fr = SpacyDetector(model="fr_core_news_sm")
guard = PromptGuard(detectors=[spacy_fr])

# German
spacy_de = SpacyDetector(model="de_core_news_sm")
guard = PromptGuard(detectors=[spacy_de])

# Or use Presidio for 50+ languages
from prompt_guard.detectors import PresidioDetector

presidio = PresidioDetector(language="es")  # Spanish
guard = PromptGuard(detectors=[presidio])
```

See [examples/multilanguage_example.py](examples/multilanguage_example.py) for more.

---

## 📖 Examples

### Basic Usage

- [Python basic](examples/python-fastapi-chat/) - FastAPI integration
- [Node/Express](examples/node-express-chat/) - Express middleware
- [Ollama local](examples/python-ollama-local/) - Local LLM

### Advanced Features

- [spaCy detector](examples/spacy_detector_example.py) - ML-based detection
- [LlamaIndex RAG](examples/llamaindex_integration_example.py) - Secure RAG
- [PostgreSQL audit](examples/postgres_audit_logging_example.py) - Compliance logging
- [Multi-language](examples/multilanguage_example.py) - International PII

### Production Deployments

- [HTTP proxy](packages/proxy/) - Zero-code integration
- [Docker](docker-compose.yml) - Container deployment
- [Kubernetes](deploy/kubernetes/) - Cloud-native deployment
- [Terraform AWS](deploy/terraform/) - Infrastructure as code

---

## 🗺️ Roadmap

### ✅ Completed (v1.2.0)

- ✅ Core library (Python)
- ✅ Async/await support
- ✅ Multiple detectors (Regex, Presidio, spaCy)
- ✅ Enterprise policies (HIPAA, PCI-DSS, GDPR)
- ✅ Caching (In-memory, Redis)
- ✅ Storage (Redis, PostgreSQL)
- ✅ Framework adapters (LangChain, LlamaIndex, Hugging Face, Vercel AI)
- ✅ HTTP proxy mode
- ✅ Docker & Kubernetes deployment
- ✅ Terraform infrastructure
- ✅ Pulumi infrastructure (Python)
- ✅ Helm chart for Kubernetes
- ✅ GitHub Actions CI/CD workflows
- ✅ Pre-commit hooks for code quality
- ✅ Comprehensive testing (100+ tests)
- ✅ Security scanning (CodeQL, Snyk, Trivy, Bandit)
- ✅ Sphinx documentation
- ✅ Load testing suite
- ✅ Multi-language support

### 🔄 In Progress (v1.3.0)

- ⏳ Node/TypeScript package (complete rewrite)
- ⏳ WASM build for browser-based detection
- ⏳ GitHub Pages documentation hosting

### 🔮 Future (v2.0.0)

- 🔮 Real-time streaming support (Server-Sent Events)
- 🔮 Custom detector SDK
- 🔮 PII discovery tool (scan databases/logs)
- 🔮 Synthetic data generation
- 🔮 Fine-grained access controls (RBAC)
- 🔮 Compliance dashboard
- 🔮 Multi-tenant support
- 🔮 Edge deployment (Cloudflare Workers, Lambda@Edge)

---

## 🔄 CI/CD & Automation

### GitHub Actions Workflows

We use GitHub Actions for continuous integration and deployment:

#### CI Workflow
- **Multi-version testing**: Python 3.9, 3.10, 3.11, 3.12, 3.13
- **Library and proxy tests**: unit, integration, security
- **Package check**: builds the wheel and smoke-tests it in a clean environment
- **Performance benchmarks**: results uploaded as an artifact
- **Node build, evaluation scripts and examples**

#### Lint Workflow
- **Python linting**: Ruff and MyPy for code quality
- **Markdown linting**: Documentation quality checks
- **YAML linting**: Configuration validation
- **Dockerfile linting**: Hadolint for Docker best practices
- **Terraform validation**: Infrastructure code checks

#### Security Workflow
- **CodeQL analysis**: GitHub's semantic code analysis
- **Snyk scanning**: Dependency vulnerability detection
- **Trivy scanning**: Container and filesystem scanning
- **Bandit**: Python security linting
- **Gitleaks**: Secret detection
- **pip-audit**: Python package vulnerability scanning
- **Dependency review**: PR dependency checks

#### Documentation Workflow
- **Sphinx build**: API documentation generation
- **GitHub Pages deployment**: Automatic doc hosting

#### Release Workflow
- **Automated releases**: Triggered on version tags
- **PyPI publishing**: Automatic package publishing
- **Docker images**: Multi-architecture builds (amd64/arm64)
- **GitHub releases**: Changelog and asset management

### Running CI Locally

```bash
# Run tests like CI
pip install -e "packages/python[dev,proxy,faker,cryptography]"
(cd packages/python && pytest tests/unit tests/integration tests/security)
(cd packages/proxy && pytest tests)

# Run linting like CI
(cd packages/python && ruff check src/ tests/ ../proxy/ && mypy src/ --ignore-missing-imports)

# Run security checks like CI
bandit -c .bandit.yml -r packages/python/src packages/proxy/src
pip-audit --skip-editable

# Run pre-commit hooks (all checks)
pre-commit run --all-files
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Areas We Need Help

- 🐛 **Bug fixes** - Check [issues](https://github.com/nik-kale/llm-slm-prompt-guard/issues)
- ✨ **New features** - See the [roadmap](docs/roadmap.md)
- 📚 **Documentation** - Improve guides and examples
- 🧪 **Testing** - Add test cases and benchmarks
- 🌍 **Internationalization** - Add language support
- 🔌 **Integrations** - New framework adapters

### Development Setup

```bash
# Clone repository
git clone https://github.com/nik-kale/llm-slm-prompt-guard.git
cd llm-slm-prompt-guard

# Install dependencies
cd packages/python
pip install -e ".[dev]"

# Install pre-commit hooks (recommended)
pip install pre-commit
pre-commit install

# Run tests
pytest tests/

# Run linting
ruff check .
mypy src/

# Build docs
cd ../../docs
make html
```

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

Configured hooks include:
- **Ruff**: Linting and formatting
- **MyPy**: Type checking
- **Bandit**: Security scanning
- **Markdown linting**: Documentation quality
- **YAML linting**: Configuration validation
- **Hadolint**: Dockerfile linting
- **Terraform format**: Infrastructure code
- **Gitleaks**: Secret detection

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Run pre-commit hooks (`pre-commit run --all-files`)
7. Update documentation
8. Commit your changes (`git commit -m 'Add amazing feature'`)
9. Push to the branch (`git push origin feature/amazing-feature`)
10. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

You are free to use this library in commercial and open-source projects.

---

## 🙏 Acknowledgments

Built with these excellent open-source projects:

- [Microsoft Presidio](https://github.com/microsoft/presidio) - ML-based PII detection
- [spaCy](https://spacy.io/) - Industrial-strength NLP
- [LangChain](https://www.langchain.com/) - LLM application framework
- [LlamaIndex](https://www.llamaindex.ai/) - Data framework for LLMs
- [Hugging Face](https://huggingface.co/) - Open-source AI ecosystem
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Redis](https://redis.io/) - In-memory data store
- [PostgreSQL](https://www.postgresql.org/) - Relational database
- [Locust](https://locust.io/) - Load testing framework

Special thanks to the LLM/SLM community for feedback and contributions!

---

## 📞 Support

### Getting Help

- 📖 **Documentation**: <https://docs.prompt-guard.com> (coming soon)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/nik-kale/llm-slm-prompt-guard/issues)
- 💡 **Feature Requests**: [GitHub Issues](https://github.com/nik-kale/llm-slm-prompt-guard/issues/new?template=feature_request.md)

### Community

- 🌟 **Star us on GitHub** if you find this useful!
- 🐦 **Follow updates** on Twitter [@promptguard](https://twitter.com/promptguard) (coming soon)
- 📧 **Email**: <support@prompt-guard.com> (coming soon)

---

## 📈 Project Stats

- **Version**: 1.2.0
- **Test Coverage**: reported by CI
- **Test Cases**: 100+
- **Lines of Code**: ~10,000+ (including infrastructure)
- **Performance**: 500+ req/s (single instance), 2,000+ req/s (with cache)
- **Supported Languages**: 10+
- **Framework Integrations**: 4+ (LangChain, LlamaIndex, Hugging Face, Vercel AI)
- **Deployment Options**: 6 (Docker, Helm/K8s, Terraform, Pulumi, Docker Compose, Manual)
- **CI/CD Workflows**: 5 (CI, Lint, Security, Docs, Release)

---

## 🎯 Who Uses This?

While still early, llm-slm-prompt-guard is designed for:

- 🏥 **Healthcare** - HIPAA-compliant AI applications
- 💳 **Finance** - PCI-DSS payment processing
- 🛡️ **Government** - Privacy-preserving AI
- 🏢 **Enterprise** - Customer support chatbots
- 🎓 **Education** - Protecting student data
- 📱 **SaaS** - Multi-tenant AI applications

**Are you using it? Let us know!** Open an [issue](https://github.com/nik-kale/llm-slm-prompt-guard/issues) to share your use case.

---

## 💻 Command Line Interface (CLI)

The `prompt-guard` CLI provides quick PII detection and anonymization without writing code.

### Installation

The CLI is included with the base package:

```bash
pip install llm-slm-prompt-guard
```

### Commands

#### Detect PII

Detect PII entities in text or files:

```bash
# Detect from text
prompt-guard detect "Contact John at john@example.com"

# Detect from file
prompt-guard detect --file document.txt

# Detect from stdin
cat document.txt | prompt-guard detect

# JSON output for CI/CD integration
prompt-guard detect --file data.txt --json-output

# Use specific policy and detectors
prompt-guard detect --policy gdpr_strict --detectors regex,presidio --file input.txt
```

#### Anonymize Text

Anonymize PII in text or files:

```bash
# Anonymize text
prompt-guard anonymize "My email is john@example.com"

# Anonymize file and save output
prompt-guard anonymize --file input.txt --output anonymized.txt

# Save mapping for de-anonymization
prompt-guard anonymize --file input.txt --output anon.txt --mapping-output mapping.json

# JSON output
prompt-guard anonymize "Contact me at 555-123-4567" --json-output
```

#### De-anonymize Text

Restore original PII from anonymized text:

```bash
# De-anonymize using mapping file
prompt-guard deanonymize "Contact [NAME_1] at [EMAIL_1]" --mapping mapping.json

# From file
prompt-guard deanonymize --file anonymized.txt --mapping mapping.json --output original.txt
```

#### Scan Directory

Batch scan files for PII:

```bash
# Scan directory for .txt files
prompt-guard scan ./documents --pattern "*.txt"

# Recursive scan
prompt-guard scan ./data --pattern "*.md" --recursive

# JSON output for reporting
prompt-guard scan ./logs --pattern "*.log" --recursive --json-output
```

#### Validate Policy

Validate custom policy YAML files:

```bash
prompt-guard validate-policy my-custom-policy.yaml
```

#### List Resources

List available policies and detectors:

```bash
# List available policies
prompt-guard list-policies

# List available detectors
prompt-guard list-detectors
```

### CLI Options

Common options across commands:

- `--policy, -p`: Policy to use (default: `default_pii`)
- `--detectors, -d`: Comma-separated detector list (default: `regex`)
- `--confidence, -c`: Minimum confidence threshold for ML detectors (default: `0.5`)
- `--json-output, -j`: Output results as JSON
- `--file, -f`: Read from file instead of argument
- `--output, -o`: Write output to file

### Examples

#### CI/CD Integration

```bash
# Check for PII in code commits
#!/bin/bash
if prompt-guard scan ./src --pattern "*.py" --json-output | jq '.total_entities > 0'; then
  echo "❌ PII detected in source code"
  exit 1
fi
```

#### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pii-detection
      name: Detect PII in files
      entry: prompt-guard scan
      args: ['.', '--pattern', '*.txt', '--pattern', '*.md']
      language: system
      pass_filenames: false
```

#### Quick Testing

```bash
# Test anonymization quickly
echo "SSN: 123-45-6789" | prompt-guard anonymize
# Output: SSN: [SSN_1]

# Check what entities are detected
echo "Call 555-123-4567 or email test@example.com" | prompt-guard detect
# Output shows: PHONE and EMAIL entities
```

---

## ⚡ Quick Commands Reference

```bash
# Installation
pip install llm-slm-prompt-guard[all]

# Run tests
pytest packages/python/tests/

# Pre-commit hooks
pre-commit install && pre-commit run --all-files

# Build docs
cd docs && make html

# Load test
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Docker
docker-compose up

# Deploy to Kubernetes (Helm)
helm install my-prompt-guard prompt-guard/prompt-guard

# Deploy to AWS (Terraform)
cd deploy/terraform && terraform apply

# Deploy to AWS (Pulumi)
cd deploy/pulumi && pulumi up

# Start HTTP proxy
python packages/proxy/src/main.py
```

---

Built with ❤️ for the LLM/SLM community.

**Version 1.2.0 | MIT License | [GitHub](https://github.com/nik-kale/llm-slm-prompt-guard)**

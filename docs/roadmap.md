# Roadmap

This document outlines the planned development roadmap for `llm-slm-prompt-guard`.

## Version 0.1 (Current) ✅

**Goal**: Minimal viable product with core functionality.

- [x] Python package structure
- [x] Node/TypeScript package structure
- [x] Core `PromptGuard` class
- [x] Regex-based detector
- [x] Basic policies (default_pii, gdpr_strict, slm_local)
- [x] Anonymization and de-anonymization
- [x] FastAPI example
- [x] Express example
- [x] Evaluation framework
- [x] Basic documentation

**Target**: Initial release for early adopters and feedback.

---

## Version 0.2 (Next)

**Goal**: Production-ready with improved detection and framework integration.

### Core Features

- [ ] **Microsoft Presidio Integration**
  - Optional dependency for ML-based PII detection
  - Better accuracy for names, locations, organizations
  - Support for multiple languages

- [ ] **Performance Optimizations**
  - Async/await support (Python `asyncio`, Node promises)
  - Batch processing API
  - Caching for repeated prompts

- [ ] **Improved Regex Patterns**
  - Better name detection (handle edge cases)
  - International phone numbers
  - More credit card formats
  - Passport numbers

### Framework Adapters

- [ ] **LangChain Adapter** (Python & JS)
  ```python
  from prompt_guard.adapters import LangChainGuard

  llm = LangChainGuard(
      llm=OpenAI(),
      policy="default_pii"
  )
  ```

- [ ] **LlamaIndex Adapter** (Python & JS)
  ```python
  from prompt_guard.adapters import LlamaIndexGuard

  query_engine = LlamaIndexGuard(
      index=index,
      policy="default_pii"
  )
  ```

### Documentation

- [ ] API reference documentation
- [ ] Integration guides
- [ ] Video tutorials

**Target**: 4-6 weeks after v0.1

---

## Version 0.3

**Goal**: Advanced detection and SLM-specific features.

### SLM-Specific Features

- [ ] **Streaming Support**
  - Real-time PII detection and masking for SSE/WebSocket
  - Important for streaming LLM/SLM responses

- [ ] **Token-Aware Anonymization**
  - Calculate token usage before/after anonymization
  - Optimize for small context windows
  - Truncation strategies

- [ ] **On-Device Optimization**
  - Minimal memory footprint mode
  - WASM build for browser-based SLMs
  - Mobile-optimized builds (iOS, Android)

### Detection Improvements

- [ ] **spaCy NER Detector**
  - Optional spaCy integration
  - Better entity recognition
  - Support for custom NER models

- [ ] **Custom Model Detector**
  - Bring your own fine-tuned model
  - Support for ONNX, TensorFlow, PyTorch

### Policies

- [ ] More industry-specific policies:
  - `hipaa_phi` - Healthcare
  - `pci_dss` - Payment card industry
  - `financial_pii` - Banking/finance
  - `edu_ferpa` - Education records

**Target**: 8-10 weeks after v0.1

---

## Version 0.4

**Goal**: Enterprise features and deployment options.

### Enterprise Features

- [ ] **Persistent Mapping Storage**
  - Redis adapter for multi-turn conversations
  - PostgreSQL adapter for audit trails
  - Encrypted storage options

- [ ] **Audit & Compliance**
  - Log all PII detections
  - Generate compliance reports
  - Export to SIEM systems

- [ ] **Context-Aware Detection**
  - Remember entities across conversation turns
  - Consistent anonymization for same user
  - Session management

### Deployment Options

- [ ] **HTTP Proxy Mode**
  - Standalone service that proxies LLM API calls
  - Drop-in replacement (no code changes)
  - OpenAI-compatible API

- [ ] **Docker Images**
  - Pre-built containers
  - Kubernetes deployment examples
  - Helm charts

- [ ] **Serverless Adapters**
  - AWS Lambda layer
  - Vercel Edge Functions
  - Cloudflare Workers

**Target**: 12-14 weeks after v0.1

---

## Version 0.5+

**Goal**: Advanced features and ecosystem growth.

### Advanced Detection

- [ ] **Multi-Language Support**
  - Non-English PII detection
  - Locale-specific policies
  - Language auto-detection

- [ ] **Pseudonymization**
  - Generate realistic but fake data
  - Maintain data format (e.g., valid email domains)
  - Reversible with secure key

- [ ] **Context-Sensitive Detection**
  - Understand context to reduce false positives
  - Domain-specific entity recognition
  - Conversation history awareness

### LLM/SLM Ecosystem Integration

- [ ] **Vercel AI SDK Adapter**
  ```typescript
  import { createPromptGuard } from 'llm-slm-prompt-guard/vercel'

  const guard = createPromptGuard()
  const stream = guard.protect(
    await openai.chat.completions.create(...)
  )
  ```

- [ ] **Hugging Face Transformers**
  ```python
  from prompt_guard.adapters import HFGuard

  pipeline = HFGuard(
      model="meta-llama/Llama-2-7b-chat-hf",
      policy="slm_local"
  )
  ```

- [ ] **Ollama Plugin**
  - Native integration with Ollama
  - Automatic PII masking for local models

### Evaluation & Benchmarking

- [ ] **Comprehensive Benchmark Suite**
  - Multi-language datasets
  - Industry-specific test cases
  - Performance benchmarks

- [ ] **LLM-Based Evaluation**
  - Use LLMs to evaluate response quality
  - Semantic similarity metrics
  - A/B testing framework

### Community & Ecosystem

- [ ] **Plugin System**
  - Third-party detectors
  - Custom anonymization strategies
  - Policy marketplace

- [ ] **Web UI**
  - Visual policy editor
  - Real-time testing interface
  - Analytics dashboard

**Target**: 16+ weeks after v0.1

---

## Long-Term Vision

### Year 1

- Establish as the go-to PII protection library for LLM/SLM apps
- Support for all major LLM/SLM frameworks
- 1000+ GitHub stars
- Active contributor community

### Year 2+

- **Federated PII Detection**: Share detection models without sharing data
- **Zero-Knowledge Proofs**: Prove PII was masked without revealing it
- **Differential Privacy**: Add noise to prevent re-identification
- **Compliance Automation**: Auto-generate compliance documentation

---

## SLM-Specific Roadmap

Given the rise of Small Language Models, we're prioritizing features specifically for SLM use cases:

### Phase 1: On-Device Optimization (v0.3)
- WASM build for browser deployment
- Minimal memory footprint (<5MB)
- Fast regex-only mode (<1ms latency)

### Phase 2: Mobile & Edge (v0.4)
- iOS/Android native libraries
- Edge device deployment (Raspberry Pi, etc.)
- Offline-first architecture

### Phase 3: SLM Framework Integration (v0.5)
- llama.cpp integration
- GGML model support
- MLX (Apple Silicon) integration
- DirectML (Windows) support

---

## How to Influence the Roadmap

We welcome community input! Here's how you can influence priorities:

1. **GitHub Issues**: Request features or report bugs
2. **Discussions**: Share use cases and requirements
3. **Pull Requests**: Contribute implementations
4. **Surveys**: Participate in quarterly roadmap surveys

**Priority is given to:**
- Features with multiple user requests
- Security and compliance improvements
- Performance optimizations
- SLM-specific innovations

---

## Release Schedule

- **Minor versions** (0.x): Every 4-6 weeks
- **Patch versions** (0.x.y): As needed for bug fixes
- **Major versions** (1.0+): When API is stable and feature-complete

---

Last updated: 2025-11-16

# Feature Opportunities Analysis

**Repository**: llm-slm-prompt-guard v1.2.0
**Analysis Date**: December 2025
**Analyst**: Automated Code Review

---

## Summary Table

| # | Feature | Category | Effort | Value | Priority |
|---|---------|----------|--------|-------|----------|
| 1 | OpenTelemetry Integration | Observability | Medium | High | 1.5 |
| 2 | Synthetic Data Replacement | Functional Enhancement | Medium | High | 1.5 |
| 3 | CLI Tool for Quick Anonymization | Developer Experience | Low | High | 3.0 |
| 4 | Confidence Threshold in Sync API | Code Quality | Low | Medium | 2.0 |
| 5 | Detection Dry-Run Mode | Functional Enhancement | Low | Medium | 2.0 |
| 6 | Rate Limiting Implementation | Security | Medium | High | 1.5 |
| 7 | Custom Anonymization Strategies | Functional Enhancement | Medium | High | 1.5 |
| 8 | Structured JSON Logging | Observability | Low | Medium | 2.0 |
| 9 | Overlapping Entity Resolution | Code Quality | Low | Medium | 2.0 |
| 10 | Pre/Post Detection Hooks | Architecture | Medium | Medium | 1.0 |

---

## Detailed Feature Requests

---

### Feature #1: OpenTelemetry Integration for Distributed Tracing

**Category**: Observability Stack

**Problem Statement**:
The current codebase has basic metrics in the HTTP proxy (`requests_total`, `requests_anonymized`, etc.) but lacks distributed tracing support. In production microservices architectures, operators cannot trace PII detection across service boundaries, making debugging latency issues and understanding request flows extremely difficult. Competitors like LLM Guard have better observability hooks.

**Proposed Solution**:
- Add optional `opentelemetry-api` and `opentelemetry-sdk` dependencies
- Instrument `PromptGuard.anonymize()` and `deanonymize()` with spans
- Add span attributes for: `pii.entity_count`, `pii.entity_types`, `pii.cache_hit`, `detector.names`
- Create context propagation in the HTTP proxy for end-to-end tracing
- Add Prometheus metrics exporter leveraging existing `prometheus-client` dependency
- Include sample Grafana dashboard JSON for common metrics

**Files to Modify**:
- `packages/python/src/prompt_guard/guard.py` (add tracing spans)
- `packages/python/src/prompt_guard/async_guard.py` (async span context)
- `packages/proxy/src/main.py` (HTTP header propagation)
- New: `packages/python/src/prompt_guard/telemetry.py`
- `packages/python/pyproject.toml` (add opentelemetry optional deps)

**Impact Assessment**:
- **Effort**: Medium (2-3 days)
- **Value**: High - Critical for production debugging and SLA monitoring
- **Priority Score**: 3/2 = 1.5

**Success Metrics**:
- Traces visible in Jaeger/Zipkin showing anonymization latency breakdown
- P95/P99 latency dashboards available in Grafana
- Detector-level latency attribution (regex vs presidio vs spacy)

---

### Feature #2: Synthetic Data Replacement (Faker Integration)

**Category**: Functional Enhancement

**Problem Statement**:
Currently, PII is replaced with placeholders like `[EMAIL_1]` or `[PERSON_1]`. While this works for de-anonymization, it makes the anonymized text look unnatural and can affect LLM response quality. Competitors like anonLLM and Presidio support replacing PII with realistic fake data (e.g., `john@example.com` → `sarah.wilson@company.org`), which produces more natural-sounding text and better LLM outputs.

**Proposed Solution**:
- Add optional `faker` library integration
- Create new anonymization strategy: `synthetic` alongside `placeholder`
- Implement `SyntheticAnonymizer` class with locale support for:
  - Names (locale-aware: English, Spanish, French, German, etc.)
  - Emails (realistic domains)
  - Phone numbers (country-specific formats)
  - Addresses, SSNs, credit cards (format-preserving)
- Maintain deterministic mapping for consistent replacement within a session
- Add `anonymization_strategy` parameter to `PromptGuard.__init__()`

**Files to Modify**:
- New: `packages/python/src/prompt_guard/anonymizers/synthetic.py`
- New: `packages/python/src/prompt_guard/anonymizers/base.py`
- `packages/python/src/prompt_guard/guard.py` (strategy selection)
- `packages/python/pyproject.toml` (add faker optional dep)
- Update tests and documentation

**Impact Assessment**:
- **Effort**: Medium (2-3 days)
- **Value**: High - Significantly improves LLM output quality
- **Priority Score**: 3/2 = 1.5

**Success Metrics**:
- LLM responses maintain natural language flow with synthetic data
- No increase in false positives from LLM misinterpreting placeholders
- User adoption rate of synthetic strategy vs placeholder

---

### Feature #3: CLI Tool for Quick Anonymization Tasks

**Category**: Developer Experience

**Problem Statement**:
There is no command-line interface for quick PII detection/anonymization tasks. Developers must write Python scripts even for simple operations like checking a file for PII or anonymizing a text snippet. This increases onboarding friction and limits utility for DevOps/security teams who may not be Python developers.

**Proposed Solution**:
- Create `prompt-guard` CLI using `click` or `typer`
- Implement commands:
  - `prompt-guard detect <text|file>` - Show detected PII entities
  - `prompt-guard anonymize <text|file> [--output]` - Anonymize and output
  - `prompt-guard deanonymize <text> --mapping <file>` - Reverse anonymization
  - `prompt-guard scan <directory> --pattern "*.txt"` - Batch scan files
  - `prompt-guard validate-policy <policy.yaml>` - Validate custom policies
- Support JSON output format for CI/CD integration
- Add `--policy`, `--detectors`, `--confidence` options
- Create entry point in pyproject.toml

**Files to Modify**:
- New: `packages/python/src/prompt_guard/cli.py`
- `packages/python/pyproject.toml` (add entry point and click/typer dep)
- Update README.md with CLI examples

**Impact Assessment**:
- **Effort**: Low (1-2 days)
- **Value**: High - Dramatically improves developer experience
- **Priority Score**: 3/1 = 3.0

**Success Metrics**:
- CLI usage in CI/CD pipelines (measurable via download stats)
- Reduced support questions about "quick testing"
- Time-to-first-detection for new users < 1 minute

---

### Feature #4: Confidence Threshold Support in Synchronous API

**Category**: Code Quality & Optimization

**Problem Statement**:
The `AsyncPromptGuard` class supports `min_confidence` filtering in `AnonymizeOptions` (line 137 of `async_guard.py`), but the synchronous `PromptGuard` class does not offer this capability. This inconsistency forces users who need confidence filtering to use the async API unnecessarily, or implement filtering manually.

**Proposed Solution**:
- Add `AnonymizeOptions` parameter to `PromptGuard.anonymize()` method
- Implement confidence-based filtering in sync guard matching async behavior
- Add `min_confidence` parameter for quick access: `guard.anonymize(text, min_confidence=0.8)`
- Update `batch_anonymize` to support options
- Ensure identical behavior between sync and async implementations

**Files to Modify**:
- `packages/python/src/prompt_guard/guard.py` (add options parameter, filtering logic)
- `packages/python/src/prompt_guard/types.py` (ensure AnonymizeOptions is exported)
- Add tests for confidence filtering

**Impact Assessment**:
- **Effort**: Low (0.5-1 day)
- **Value**: Medium - Improves API consistency and usability
- **Priority Score**: 2/1 = 2.0

**Success Metrics**:
- API parity between sync and async implementations
- Reduced false positive rates when using confidence thresholds
- No breaking changes for existing users

---

### Feature #5: Detection Dry-Run Mode (Preview Without Anonymization)

**Category**: Functional Enhancement

**Problem Statement**:
Users cannot preview what PII would be detected without actually performing anonymization. This makes it difficult to tune detector configurations, debug false positives, or generate compliance reports showing what types of PII exist in a dataset without modifying the data.

**Proposed Solution**:
- Add `detect_only()` method to `PromptGuard` returning `List[DetectorResult]`
- Include entity statistics: count per type, confidence distribution, positions
- Add `--dry-run` flag to CLI (Feature #3)
- Create `DetectionReport` dataclass with:
  - `entities: List[DetectorResult]`
  - `summary: Dict[str, int]` (count per entity type)
  - `coverage: float` (% of text that is PII)
  - `risk_score: str` (low/medium/high based on entity types)
- Support JSON/HTML report export

**Files to Modify**:
- `packages/python/src/prompt_guard/guard.py` (add detect_only method)
- `packages/python/src/prompt_guard/async_guard.py` (async version)
- New: `packages/python/src/prompt_guard/report.py` (DetectionReport)
- `packages/python/src/prompt_guard/types.py` (new types)

**Impact Assessment**:
- **Effort**: Low (1-2 days)
- **Value**: Medium - Enables compliance auditing and debugging
- **Priority Score**: 2/1 = 2.0

**Success Metrics**:
- Ability to generate PII audit reports for compliance teams
- Faster detector tuning workflow
- Integration with security scanning pipelines

---

### Feature #6: Rate Limiting Implementation for HTTP Proxy

**Category**: Security Posture

**Problem Statement**:
The HTTP proxy has a `rate_limit: Optional[int] = None` configuration option (line 59 of `main.py`) but it is not implemented. Without rate limiting, the proxy is vulnerable to abuse, DoS attacks, and runaway costs from excessive LLM API calls. The security tests also have placeholder tests for rate limiting (`test_rate_limiting` at line 276) that do nothing.

**Proposed Solution**:
- Implement token bucket rate limiting using Redis as backend
- Support per-IP, per-user (via X-User-ID header), and global rate limits
- Add configurable limits: `requests_per_minute`, `requests_per_hour`
- Return `429 Too Many Requests` with `Retry-After` header when exceeded
- Add rate limit metrics: `rate_limit_exceeded_total`, `rate_limit_remaining`
- Implement burst allowance configuration
- Support bypass for trusted IPs (internal services)

**Files to Modify**:
- `packages/proxy/src/main.py` (implement rate limiting middleware)
- New: `packages/proxy/src/rate_limiter.py` (token bucket implementation)
- `packages/python/tests/security/test_security.py` (implement real tests)
- Update deployment docs with rate limit configuration

**Impact Assessment**:
- **Effort**: Medium (2 days)
- **Value**: High - Critical security hardening
- **Priority Score**: 3/2 = 1.5

**Success Metrics**:
- No successful DoS attacks in penetration testing
- Abuse detection via rate limit exceeded metrics
- Configurable limits per tenant in multi-tenant deployments

---

### Feature #7: Custom Anonymization Strategies (Hash, Mask, Encrypt)

**Category**: Functional Enhancement

**Problem Statement**:
The library only supports placeholder replacement for anonymization. Many enterprise use cases require alternative strategies: hashing for analytics (preserving uniqueness), partial masking for display (`john@***.com`), or encryption for reversible protection with key management. Competitors like pii-anonymizer support multiple modes including SHA256 hashing and Fernet encryption.

**Proposed Solution**:
- Create `AnonymizationStrategy` enum: `PLACEHOLDER`, `HASH`, `MASK`, `ENCRYPT`, `SYNTHETIC`
- Implement strategy classes:
  - `HashAnonymizer`: SHA256/SHA512 with optional salt for consistent hashing
  - `MaskAnonymizer`: Configurable masking patterns (`****`, `[REDACTED]`, partial reveal)
  - `EncryptAnonymizer`: Fernet (AES) encryption with key management
- Make strategies configurable per entity type in policies:
  ```yaml
  entities:
    EMAIL:
      strategy: mask
      mask_pattern: "****@****.***"
    SSN:
      strategy: hash
      algorithm: sha256
  ```
- Support strategy chaining (hash + mask)

**Files to Modify**:
- New: `packages/python/src/prompt_guard/anonymizers/` directory
- New: `hash.py`, `mask.py`, `encrypt.py`, `base.py`
- `packages/python/src/prompt_guard/guard.py` (strategy selection)
- Policy YAML schema updates
- `packages/python/pyproject.toml` (cryptography dep for encrypt)

**Impact Assessment**:
- **Effort**: Medium (3-4 days)
- **Value**: High - Unlocks enterprise use cases
- **Priority Score**: 3/2 = 1.5

**Success Metrics**:
- Support for analytics pipelines using hashed PII
- GDPR Article 32 compliance with encryption strategy
- Adoption by finance/healthcare customers requiring specific strategies

---

### Feature #8: Structured JSON Logging with Correlation IDs

**Category**: Observability Stack

**Problem Statement**:
Current logging uses Python's basic logging format (line 42-46 in `main.py`). In production environments, unstructured logs are difficult to query, correlate across services, and ingest into log aggregation systems (ELK, Splunk, Datadog). There's no request correlation ID support for tracing individual requests through the system.

**Proposed Solution**:
- Implement structured JSON logging using `structlog` or `python-json-logger`
- Add automatic context enrichment:
  - `request_id`: UUID for each request
  - `session_id`: PII session identifier
  - `user_id`: From X-User-ID header
  - `detector_name`: Which detector found PII
  - `pii_entity_types`: Types detected (without values)
  - `latency_ms`: Operation duration
- Propagate correlation ID through async operations
- Configure log levels per component (detectors, storage, proxy)
- Ensure PII values are NEVER logged (verify with tests)

**Files to Modify**:
- New: `packages/python/src/prompt_guard/logging.py`
- `packages/proxy/src/main.py` (replace basic logging setup)
- `packages/python/src/prompt_guard/storage/redis_storage.py`
- `packages/python/src/prompt_guard/storage/postgres_storage.py`
- Add log sanitization tests

**Impact Assessment**:
- **Effort**: Low (1-2 days)
- **Value**: Medium - Improves production debuggability
- **Priority Score**: 2/1 = 2.0

**Success Metrics**:
- Logs parseable by ELK/Splunk/Datadog without custom parsing rules
- Request traces via correlation ID across all components
- Zero PII leakage in logs (verified by security tests)

---

### Feature #9: Improved Overlapping Entity Resolution

**Category**: Code Quality & Optimization

**Problem Statement**:
When multiple detectors find overlapping entities (e.g., regex finds "John Smith" as PERSON, presidio finds "John" as PERSON), the current implementation in `guard.py` simply sorts by start index and processes sequentially. This can lead to duplicate detections, inconsistent results, or missing entities. The `EnhancedRegexDetector` (line 248-253) has overlap handling, but core `PromptGuard` does not.

**Proposed Solution**:
- Implement proper overlapping entity resolution in `PromptGuard._resolve_overlaps()`
- Resolution strategies:
  - **Longest Match**: Prefer longer spans
  - **Highest Confidence**: Prefer higher confidence scores
  - **Priority**: Prefer detectors in order specified
  - **Merge**: Combine overlapping entities of same type
- Make strategy configurable: `guard = PromptGuard(overlap_strategy="longest_match")`
- Add unit tests for various overlap scenarios
- Document behavior in API docs

**Files to Modify**:
- `packages/python/src/prompt_guard/guard.py` (add _resolve_overlaps method)
- `packages/python/src/prompt_guard/async_guard.py` (same logic)
- `packages/python/src/prompt_guard/types.py` (OverlapStrategy enum)
- Add comprehensive overlap tests

**Impact Assessment**:
- **Effort**: Low (1-2 days)
- **Value**: Medium - Improves detection accuracy
- **Priority Score**: 2/1 = 2.0

**Success Metrics**:
- No duplicate placeholders in output
- Consistent results when using multiple detectors
- Improved F1 score in detection benchmarks

---

### Feature #10: Pre/Post Detection Hooks (Event System)

**Category**: Architecture & Scalability

**Problem Statement**:
There's no way to hook into the detection/anonymization lifecycle for custom behavior. Users cannot: log specific detection events to external systems, trigger alerts on high-risk PII types, modify detection results before anonymization, or integrate with custom compliance workflows without forking the library.

**Proposed Solution**:
- Implement event hook system with callbacks:
  - `on_detection(entity: DetectorResult)` - Called for each entity found
  - `on_pre_anonymize(text: str, entities: List[DetectorResult])` - Before anonymization
  - `on_post_anonymize(original: str, anonymized: str, mapping: Mapping)` - After
  - `on_error(error: Exception, context: Dict)` - On any error
- Allow multiple hooks per event
- Support both sync and async hooks
- Implement `HookRegistry` for registration
- Add common built-in hooks:
  - `AlertHook`: Send webhook on high-risk entity types
  - `MetricsHook`: Emit custom metrics
  - `AuditHook`: Detailed audit logging

**Files to Modify**:
- New: `packages/python/src/prompt_guard/hooks.py`
- `packages/python/src/prompt_guard/guard.py` (invoke hooks)
- `packages/python/src/prompt_guard/async_guard.py` (async hooks)
- Add examples and documentation

**Impact Assessment**:
- **Effort**: Medium (2-3 days)
- **Value**: Medium - Enables extensibility without forking
- **Priority Score**: 2/2 = 1.0

**Success Metrics**:
- Custom integrations possible without library modifications
- Webhook alerts for compliance teams on SSN/credit card detection
- Third-party hook ecosystem development

---

## Competitive Analysis

| Feature | llm-slm-prompt-guard | LLM Guard | anonLLM | Presidio |
|---------|---------------------|-----------|---------|----------|
| Regex Detection | ✅ | ✅ | ✅ | ❌ |
| ML Detection (Presidio) | ✅ | ✅ | ✅ | ✅ |
| spaCy NER | ✅ | ✅ | ❌ | ✅ |
| De-anonymization | ✅ | ❌ | ✅ | ❌ |
| Synthetic Data | ❌ | ❌ | ❌ | ✅ |
| LangChain Adapter | ✅ | ✅ | ❌ | ❌ |
| LlamaIndex Adapter | ✅ | ❌ | ❌ | ✅ |
| HTTP Proxy | ✅ | ❌ | ❌ | ❌ |
| Rate Limiting | ❌ | ❌ | ❌ | N/A |
| CLI Tool | ❌ | ❌ | ❌ | ✅ |
| Compliance Policies | ✅ | ✅ | ❌ | ❌ |
| Distributed Tracing | ❌ | ❌ | ❌ | ❌ |
| Multi-language | ✅ | ✅ | Limited | ✅ |

**Key Gaps vs Competitors**:
1. No CLI tool (Presidio has one)
2. No synthetic data replacement (Presidio supports Faker)
3. No rate limiting (security gap)
4. No distributed tracing (observability gap)

---

## Implementation Priority Roadmap

### Phase 1: Quick Wins (Week 1)
1. **CLI Tool** (Priority 3.0) - Immediate developer experience improvement
2. **Confidence Threshold in Sync API** (Priority 2.0) - API consistency
3. **Detection Dry-Run Mode** (Priority 2.0) - Enables compliance workflows

### Phase 2: Security & Observability (Week 2)
4. **Rate Limiting** (Priority 1.5) - Critical security hardening
5. **Structured JSON Logging** (Priority 2.0) - Production readiness
6. **Overlapping Entity Resolution** (Priority 2.0) - Detection quality

### Phase 3: Feature Parity (Week 3-4)
7. **OpenTelemetry Integration** (Priority 1.5) - Enterprise observability
8. **Synthetic Data Replacement** (Priority 1.5) - LLM output quality
9. **Custom Anonymization Strategies** (Priority 1.5) - Enterprise flexibility

### Phase 4: Extensibility (Week 4+)
10. **Pre/Post Detection Hooks** (Priority 1.0) - Long-term extensibility

---

## Notes for Implementers

1. **Backward Compatibility**: All features should be additive; existing API must remain unchanged
2. **Optional Dependencies**: New dependencies (faker, opentelemetry, etc.) must be optional
3. **Test Coverage**: Each feature requires unit tests and integration tests
4. **Documentation**: Update README, API docs, and add examples for each feature
5. **Performance**: Run benchmarks before/after to ensure no regression

---

*Generated by automated codebase analysis*

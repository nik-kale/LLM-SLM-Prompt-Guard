# Architecture

## Overview

`llm-slm-prompt-guard` is designed as a modular, pluggable system for PII detection and anonymization in LLM/SLM applications.

## High-Level Flow

```
┌──────────────┐
│  User Input  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│         PromptGuard                      │
│  ┌────────────────────────────────────┐  │
│  │  1. Detection Phase                │  │
│  │     - Run all configured detectors │  │
│  │     - Collect PII entities         │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  2. Anonymization Phase            │  │
│  │     - Apply policy rules           │  │
│  │     - Replace PII with placeholders│  │
│  │     - Build mapping table          │  │
│  └────────────────────────────────────┘  │
└──────────┬───────────────────────────────┘
           │
           ▼
    ┌──────────────┐
    │  Anonymized  │
    │    Prompt    │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  LLM/SLM API │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   Response   │
    └──────┬───────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  De-anonymization (Optional)             │
│  - Replace placeholders with originals   │
└──────────┬───────────────────────────────┘
           │
           ▼
    ┌──────────────┐
    │ Final Output │
    └──────────────┘
```

## Core Components

### 1. Detectors

Detectors are responsible for identifying PII in text. They implement a simple interface:

```python
class BaseDetector(ABC):
    @abstractmethod
    def detect(self, text: str) -> List[DetectorResult]:
        pass
```

**Built-in Detectors:**
- `RegexDetector`: Pattern-based detection using regular expressions
  - Fast and lightweight
  - No external dependencies
  - Good for common PII patterns (emails, phones, IPs, SSNs)

**Future Detectors:**
- `PresidioDetector`: Microsoft Presidio integration (ML-based)
- `SpacyDetector`: spaCy NER-based detection
- `CustomModelDetector`: For fine-tuned models

### 2. Policies

Policies define:
- Which PII types to detect
- How to anonymize each type (placeholder format)
- Future: Masking strategies (replace, redact, pseudonymize)

**Example Policy (YAML):**
```yaml
name: default_pii
description: Basic PII masking
entities:
  EMAIL:
    placeholder: "[EMAIL_{i}]"
  PERSON:
    placeholder: "[NAME_{i}]"
  PHONE:
    placeholder: "[PHONE_{i}]"
```

**Built-in Policies:**
- `default_pii`: Basic PII types
- `gdpr_strict`: EU GDPR-compliant
- `slm_local`: Optimized for local/on-device SLMs

### 3. PromptGuard

The main orchestrator that:
1. Coordinates multiple detectors
2. Applies policy rules
3. Manages the mapping table
4. Handles de-anonymization

**Key Methods:**
- `anonymize(text: str) -> (str, Mapping)`: Anonymize text
- `deanonymize(text: str, mapping: Mapping) -> str`: Restore original values

### 4. Mapping Table

A simple dictionary that maps placeholders back to original values:

```python
{
  "[EMAIL_1]": "john@example.com",
  "[NAME_1]": "John Smith",
  "[PHONE_1]": "555-123-4567"
}
```

**Storage Options (Future):**
- In-memory (default, for single requests)
- Redis (for multi-turn conversations)
- Encrypted database (for persistent storage)

## Design Principles

### 1. Framework Agnostic

Works with any LLM/SLM provider or framework:
- Direct API calls (OpenAI, Anthropic, etc.)
- LangChain, LlamaIndex
- Vercel AI SDK, Hugging Face
- Local models (Ollama, llama.cpp)

### 2. Composable

- Mix and match detectors
- Switch policies dynamically
- Extend with custom detectors/policies

### 3. Privacy-First

- No data sent to external services (by default)
- Mapping tables can be stored securely
- Audit trail support (future)

### 4. Performance

- Minimal overhead (<10ms for typical prompts)
- Async support (future)
- Batch processing support (future)

### 5. SLM-Optimized

Special considerations for Small Language Models:
- **Lightweight detection**: Minimal CPU/memory overhead for on-device inference
- **Shorter placeholders**: SLMs have smaller context windows
- **Simplified policies**: Fewer entity types to reduce complexity
- **Local-first**: No external API calls for detection

## Extension Points

### Custom Detectors

```python
from prompt_guard.detectors import BaseDetector

class MyCustomDetector(BaseDetector):
    def detect(self, text: str) -> List[DetectorResult]:
        # Your detection logic
        return results
```

### Custom Policies

Create a YAML file:

```yaml
name: my_custom_policy
entities:
  MY_TYPE:
    placeholder: "[CUSTOM_{i}]"
```

Load it:

```python
guard = PromptGuard(
    detectors=["regex"],
    custom_policy_path="/path/to/my_policy.yaml"
)
```

## Performance Characteristics

### Latency

| Component | Typical Time |
|-----------|--------------|
| Regex Detection | <5ms |
| Anonymization | <2ms |
| De-anonymization | <1ms |
| **Total** | **<10ms** |

*Measured on typical prompts (~200 words)*

### Memory

- Base memory footprint: ~10MB (Python), ~5MB (Node)
- Per-request overhead: ~1KB

### Scalability

- **Stateless**: Each request is independent
- **Horizontally scalable**: Deploy multiple instances
- **Concurrent**: Thread-safe/async-safe

## Future Architecture

### Planned Enhancements

1. **Streaming Support**
   - Detect and anonymize in real-time as text arrives
   - Important for SSE/WebSocket responses

2. **Context-Aware Detection**
   - Remember PII across conversation turns
   - Consistent anonymization for same entities

3. **Reversible Pseudonymization**
   - Generate realistic but fake data
   - Better LLM understanding than placeholders

4. **Audit & Compliance**
   - Log all PII detections
   - Export compliance reports

5. **Multi-Language**
   - Support for non-English PII
   - Locale-specific policies

6. **HTTP Proxy Mode**
   - Drop-in replacement for any LLM API
   - No code changes required

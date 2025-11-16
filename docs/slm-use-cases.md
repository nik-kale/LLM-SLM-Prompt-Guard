# SLM-Specific Use Cases

This document outlines use cases and optimizations specifically for Small Language Models (SLMs).

## Why SLMs Need Special Consideration

Small Language Models differ from large cloud-based LLMs in several key ways:

| Aspect | Large LLMs | Small LLMs (SLMs) |
|--------|------------|-------------------|
| **Deployment** | Cloud API | On-device, edge, local |
| **Context Window** | 32k-128k+ tokens | 2k-8k tokens |
| **Privacy** | Data sent to cloud | Data stays local |
| **Latency** | 100-1000ms | 10-100ms |
| **Resource Usage** | High (cloud) | Constrained (mobile/edge) |

**Key Implication**: PII protection for SLMs must be:
- ⚡ **Lightweight** (minimal CPU/memory overhead)
- 🎯 **Token-efficient** (shorter placeholders to save context)
- 🔒 **Privacy-first** (no external API calls)
- 📱 **Mobile-ready** (work in constrained environments)

---

## Use Case 1: Mobile Personal Assistant

### Scenario
A mobile app with an on-device SLM that helps users manage their daily tasks and emails.

### Challenge
- User data contains PII (names, emails, phone numbers)
- SLM runs locally on mobile device
- Limited RAM (2-4GB available for inference)
- Small context window (2048 tokens)

### Solution

```python
from prompt_guard import PromptGuard

# Use SLM-optimized policy
guard = PromptGuard(
    detectors=["regex"],  # Lightweight, no ML models
    policy="slm_local"    # Shorter placeholders
)

# User input from email
user_input = """
Hi, please schedule a meeting with John Smith (john.smith@company.com)
and Sarah Johnson (sarah.j@company.com) for tomorrow at 2 PM.
My phone is 555-123-4567 if they need to reach me.
"""

# Anonymize before sending to on-device SLM
anonymized, mapping = guard.anonymize(user_input)
print(anonymized)
# Output: "Hi, please schedule a meeting with [USER_1] ([EMAIL_1])
# and [USER_2] ([EMAIL_2]) for tomorrow at 2 PM.
# My phone is [PHONE_1] if they need to reach me."

# Send to local SLM (e.g., using llama.cpp, GGML, etc.)
# response = local_slm.generate(anonymized)

# De-anonymize the response
# final_response = guard.deanonymize(response, mapping)
```

### Benefits
- **Privacy**: PII never leaves the device
- **Efficiency**: Regex detection adds <1ms overhead
- **Token savings**: `[USER_1]` uses fewer tokens than `[PERSON_NAME_1]`
- **No network**: Works offline

---

## Use Case 2: Edge Device IoT Gateway

### Scenario
An edge gateway that processes natural language commands for smart home devices.

### Challenge
- Runs on Raspberry Pi or similar edge device
- Limited memory (1-2GB)
- Must work offline
- Handles family member names, emails, and preferences

### Solution

```python
from prompt_guard import PromptGuard
import resource  # Monitor memory usage

# Initialize with minimal footprint
guard = PromptGuard(
    detectors=["regex"],
    policy="slm_local"
)

# Edge device processing
def process_command(command: str) -> str:
    # Track memory
    start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    # Anonymize (very fast on edge devices)
    anonymized, mapping = guard.anonymize(command)

    # Memory overhead is minimal (~1KB)
    end_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"Memory overhead: {end_mem - start_mem} KB")

    # Send to local SLM for intent recognition
    # intent = slm.classify(anonymized)

    # De-anonymize if needed
    # return guard.deanonymize(intent, mapping)
    return anonymized

# Example
command = "Set the thermostat to 72 degrees and notify john@family.com"
result = process_command(command)
```

### Benefits
- **Low overhead**: Works on constrained hardware
- **Fast**: <1ms latency for PII detection
- **Offline**: No cloud dependencies
- **Privacy**: Family data stays on local network

---

## Use Case 3: Healthcare Chat Assistant

### Scenario
A clinic's internal chat assistant using a local SLM for patient triage.

### Challenge
- HIPAA compliance required
- Patient names, DOB, medical record numbers
- SLM has limited context (4096 tokens)
- Must work even if internet is down

### Solution

Create a custom policy for healthcare:

```yaml
# packages/python/src/prompt_guard/policies/hipaa_phi.yaml
name: hipaa_phi
description: HIPAA-compliant PHI masking for healthcare SLMs
entities:
  PERSON:
    placeholder: "[PT_{i}]"      # Patient - shorter than [PATIENT_{i}]
  EMAIL:
    placeholder: "[EMAIL_{i}]"
  PHONE:
    placeholder: "[PHONE_{i}]"
  SSN:
    placeholder: "[ID_{i}]"
  # Medical-specific
  MRN:  # Medical Record Number
    placeholder: "[MRN_{i}]"
  DATE_OF_BIRTH:
    placeholder: "[DOB_{i}]"
```

Usage:

```python
from prompt_guard import PromptGuard

# Custom detector for medical entities
class MedicalDetector(BaseDetector):
    def detect(self, text: str) -> List[DetectorResult]:
        results = []

        # Detect MRN (format: MRN-123456)
        mrn_pattern = re.compile(r"\bMRN-\d{6}\b")
        for match in mrn_pattern.finditer(text):
            results.append(DetectorResult(
                entity_type="MRN",
                start=match.start(),
                end=match.end(),
                text=match.group(0)
            ))

        return results

# Initialize with custom detector and policy
guard = PromptGuard(
    detectors=[MedicalDetector()],
    custom_policy_path="./hipaa_phi.yaml"
)

# Patient intake form
intake = """
Patient: Sarah Johnson
DOB: 1985-03-15
MRN: MRN-123456
Email: sarah.j@email.com
Phone: 555-987-6543
Chief complaint: fever and cough for 3 days
"""

anonymized, mapping = guard.anonymize(intake)
# Send to local medical SLM for triage
# triage_result = medical_slm.triage(anonymized)
```

### Benefits
- **HIPAA Compliant**: PHI is masked
- **Local processing**: No cloud = no data breach risk
- **Token efficient**: Short placeholders for small context
- **Audit trail**: Can log anonymized queries safely

---

## Use Case 4: Corporate Knowledge Assistant

### Scenario
A company deploys a local SLM to answer employee questions about internal docs.

### Challenge
- Documents contain employee names, emails, project codes
- SLM runs on company servers (not cloud)
- Logs must not contain PII for compliance
- Context window limited to 8192 tokens

### Solution

```python
from prompt_guard import PromptGuard
import logging

# Custom policy for corporate environment
guard = PromptGuard(
    detectors=["regex"],
    policy="default_pii"  # or create corporate_pii.yaml
)

# Setup logging with anonymization
class AnonymizingLogger:
    def __init__(self, logger, guard):
        self.logger = logger
        self.guard = guard

    def log_query(self, query: str, response: str):
        # Anonymize before logging
        anon_query, _ = self.guard.anonymize(query)
        anon_response, _ = self.guard.anonymize(response)

        self.logger.info({
            "query": anon_query,
            "response": anon_response,
            "timestamp": datetime.now().isoformat()
        })

# Usage
logger = AnonymizingLogger(logging.getLogger("app"), guard)

query = "What's the status of Project Phoenix? Contact alice@company.com for details."
anonymized_query, mapping = guard.anonymize(query)

# Send to local SLM
# response = company_slm.ask(anonymized_query)

# Log anonymized version
# logger.log_query(query, response)

# Return de-anonymized response to user
# final_response = guard.deanonymize(response, mapping)
```

### Benefits
- **Safe logging**: Logs don't contain PII
- **Compliance**: Meet data retention policies
- **Local**: Sensitive data doesn't leave the company
- **Efficient**: Works with SLM context limits

---

## Use Case 5: Browser Extension with Local SLM

### Scenario
A browser extension that uses WebAssembly-based SLM to help with writing emails.

### Challenge
- Runs entirely in the browser
- Limited memory (browser sandbox)
- Must work offline
- User emails contain PII

### Solution (JavaScript/TypeScript)

```typescript
import { PromptGuard } from 'llm-slm-prompt-guard';
// Assuming a WASM-based SLM like transformers.js

const guard = new PromptGuard({
  detectors: ['regex'],
  policy: 'slm_local'
});

// Browser extension content script
async function rewriteEmail(emailDraft: string): Promise<string> {
  // Anonymize email draft
  const { anonymized, mapping } = guard.anonymize(emailDraft);

  // Send to local WASM SLM
  // const suggestions = await localSLM.generateSuggestions(anonymized);

  // De-anonymize suggestions
  // const finalSuggestions = guard.deanonymize(suggestions, mapping);

  return anonymized;
}

// Example
const draft = `
Hi John,

Please send the proposal to sarah@client.com by EOD.
My number is 555-123-4567 if you have questions.

Thanks!
`;

rewriteEmail(draft).then(console.log);
```

### Benefits
- **Privacy**: Email content never leaves browser
- **Fast**: Pure regex, no ML overhead
- **Lightweight**: Small bundle size
- **Offline**: Works without internet

---

## Use Case 6: Development Tools with Local Code Models

### Scenario
An IDE plugin using a local code generation SLM (e.g., StarCoder, CodeLlama).

### Challenge
- Code contains API keys, tokens, emails in comments
- Must work offline (some devs have no internet)
- Context limited (code models have smaller windows)
- Real-time performance needed

### Solution

```python
from prompt_guard import PromptGuard

# Custom policy for code
guard = PromptGuard(
    detectors=["regex"],
    custom_policy_path="./dev_secrets.yaml"
)

# Custom detector for API keys and tokens
class SecretDetector(BaseDetector):
    def detect(self, text: str) -> List[DetectorResult]:
        results = []

        # Detect common API key patterns
        api_key_patterns = [
            r'sk-[a-zA-Z0-9]{32,}',  # OpenAI
            r'ghp_[a-zA-Z0-9]{36}',   # GitHub
            r'AKIA[A-Z0-9]{16}',      # AWS
        ]

        for pattern in api_key_patterns:
            regex = re.compile(pattern)
            for match in regex.finditer(text):
                results.append(DetectorResult(
                    entity_type="API_KEY",
                    start=match.start(),
                    end=match.end(),
                    text=match.group(0)
                ))

        return results

# IDE plugin integration
def assist_with_code(code_snippet: str) -> str:
    # Anonymize secrets before sending to local SLM
    anonymized, mapping = guard.anonymize(code_snippet)

    # Generate code with local SLM
    # completion = code_slm.complete(anonymized)

    # De-anonymize (usually not needed for code completion)
    # return guard.deanonymize(completion, mapping)
    return anonymized

# Example
code = """
# Contact: developer@company.com
# API Key: sk-abc123xyz789...
import openai
openai.api_key = "sk-abc123xyz789..."
"""

safe_code = assist_with_code(code)
```

### Benefits
- **No secret leaks**: API keys masked before SLM
- **Safe sharing**: Can share logs without exposing secrets
- **Fast**: <1ms overhead
- **Offline**: Works with local code models

---

## Performance Optimizations for SLMs

### 1. Token-Efficient Placeholders

```yaml
# Standard policy
PERSON:
  placeholder: "[PERSON_NAME_{i}]"  # ~5 tokens

# SLM-optimized policy
PERSON:
  placeholder: "[U_{i}]"  # ~2 tokens
```

**Savings**: 60% fewer tokens for placeholders

### 2. Minimal Detection Scope

Only detect PII types you actually need:

```python
# Don't do this for SLMs
guard = PromptGuard(
    detectors=["regex", "spacy", "presidio"],  # Too heavy!
    policy="detect_everything"
)

# Do this instead
guard = PromptGuard(
    detectors=["regex"],  # Lightweight
    policy="slm_local"     # Only essential PII types
)
```

### 3. Batch Processing

For offline/batch scenarios:

```python
# Process multiple prompts at once
prompts = [prompt1, prompt2, prompt3]
results = [guard.anonymize(p) for p in prompts]

# Even better: use multiprocessing for large batches
from multiprocessing import Pool

with Pool(4) as pool:
    results = pool.map(guard.anonymize, prompts)
```

### 4. Caching for Repeated Content

```python
from functools import lru_cache

class CachedGuard(PromptGuard):
    @lru_cache(maxsize=1000)
    def anonymize(self, text: str):
        return super().anonymize(text)

# Reuse for repeated prompts
guard = CachedGuard(policy="slm_local")
```

---

## SLM Framework Integration Examples

### Ollama (Local Models)

```python
import ollama
from prompt_guard import PromptGuard

guard = PromptGuard(policy="slm_local")

def chat_with_ollama(message: str, model="llama2"):
    anonymized, mapping = guard.anonymize(message)

    response = ollama.chat(
        model=model,
        messages=[{'role': 'user', 'content': anonymized}]
    )

    return guard.deanonymize(response['message']['content'], mapping)
```

### llama.cpp (GGML Models)

```python
from llama_cpp import Llama
from prompt_guard import PromptGuard

llm = Llama(model_path="./models/llama-2-7b-chat.gguf")
guard = PromptGuard(policy="slm_local")

def generate(prompt: str, max_tokens=256):
    anonymized, mapping = guard.anonymize(prompt)

    output = llm(
        anonymized,
        max_tokens=max_tokens,
        temperature=0.7
    )

    return guard.deanonymize(output['choices'][0]['text'], mapping)
```

### GPT4All (Desktop Models)

```python
from gpt4all import GPT4All
from prompt_guard import PromptGuard

model = GPT4All("orca-mini-3b-gguf2-q4_0.gguf")
guard = PromptGuard(policy="slm_local")

def chat(message: str):
    anonymized, mapping = guard.anonymize(message)
    response = model.generate(anonymized)
    return guard.deanonymize(response, mapping)
```

---

## Best Practices for SLMs

1. **Choose lightweight detection**: Use regex over ML models
2. **Optimize placeholders**: Shorter = more context for SLM
3. **Only detect what you need**: Don't over-mask
4. **Test on target device**: Verify performance on actual hardware
5. **Monitor resource usage**: Measure CPU, memory, latency
6. **Cache when possible**: Reuse results for repeated inputs
7. **Document tradeoffs**: Know what you're sacrificing

---

## Benchmarks

Coming soon: Performance benchmarks for common SLM scenarios.

---

## Contributing SLM Use Cases

Have a unique SLM use case? We'd love to hear about it!

Open an issue or discussion to share your use case and we'll add it to this document.

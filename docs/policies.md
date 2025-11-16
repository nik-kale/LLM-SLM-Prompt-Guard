# Policies

Policies define how `llm-slm-prompt-guard` detects and anonymizes PII. They are configured using YAML files.

## Policy Structure

```yaml
name: policy_name
description: Human-readable description
entities:
  ENTITY_TYPE:
    placeholder: "[PLACEHOLDER_{i}]"
    # Future fields:
    # strategy: "replace" | "redact" | "pseudonymize"
    # confidence_threshold: 0.8
```

## Built-in Policies

### 1. default_pii

**Purpose**: General-purpose PII masking for most applications.

**Detects:**
- `EMAIL`: Email addresses
- `PHONE`: Phone numbers
- `PERSON`: Person names
- `IP_ADDRESS`: IP addresses
- `CREDIT_CARD`: Credit card numbers
- `SSN`: Social Security Numbers

**Example:**
```python
guard = PromptGuard(policy="default_pii")
```

**Use Cases:**
- Customer support chatbots
- General-purpose AI assistants
- Internal tools

---

### 2. gdpr_strict

**Purpose**: Strict GDPR-compliant PII masking for EU applications.

**Detects**: All types from `default_pii` with EU-specific placeholder formats.

**Differences from default:**
- More generic placeholder names (e.g., `[PERSON_{i}]` instead of `[NAME_{i}]`)
- Designed for GDPR Article 32 compliance
- Suitable for data minimization requirements

**Example:**
```python
guard = PromptGuard(policy="gdpr_strict")
```

**Use Cases:**
- EU-based applications
- GDPR compliance requirements
- Data protection by design

---

### 3. slm_local

**Purpose**: Optimized for local/on-device Small Language Model (SLM) usage.

**Detects**: Same types as `default_pii` but with shorter placeholders.

**Key Features:**
- **Shorter placeholders**: Reduce token usage (critical for SLMs with limited context)
- **Privacy-first**: Designed for scenarios where data never leaves the device
- **Lightweight**: Minimal overhead for resource-constrained environments

**Placeholder Format:**
- `[EMAIL_{i}]` → Used for emails
- `[USER_{i}]` → Used for person names (shorter than `[PERSON_{i}]`)
- `[ADDR_{i}]` → Used for IP addresses (shorter)

**Example:**
```python
guard = PromptGuard(policy="slm_local")
```

**Use Cases:**
- On-device AI (mobile apps, edge devices)
- Offline chatbots
- Privacy-sensitive applications
- Resource-constrained environments

---

## Creating Custom Policies

### 1. Define Your Policy YAML

Create a file `my_policy.yaml`:

```yaml
name: my_custom_policy
description: Policy for my specific use case
entities:
  EMAIL:
    placeholder: "[EMAIL_{i}]"
  EMPLOYEE_ID:
    placeholder: "[EMP_{i}]"
  API_KEY:
    placeholder: "[KEY_{i}]"
```

### 2. Load the Policy

**Python:**
```python
from prompt_guard import PromptGuard

guard = PromptGuard(
    detectors=["regex"],
    custom_policy_path="./my_policy.yaml"
)
```

**Node/TypeScript:**
```typescript
import { PromptGuard } from "llm-slm-prompt-guard";

const guard = new PromptGuard({
  detectors: ["regex"],
  customPolicyPath: "./my_policy.yaml"
});
```

### 3. Custom Entity Types

To detect custom entity types, you'll need a custom detector:

**Python:**
```python
import re
from prompt_guard.detectors import BaseDetector
from prompt_guard.types import DetectorResult

class MyCustomDetector(BaseDetector):
    def detect(self, text: str) -> list:
        results = []
        # Detect employee IDs (format: EMP-12345)
        emp_pattern = re.compile(r"\bEMP-\d{5}\b")
        for match in emp_pattern.finditer(text):
            results.append(DetectorResult(
                entity_type="EMPLOYEE_ID",
                start=match.start(),
                end=match.end(),
                text=match.group(0)
            ))
        return results

# Use it
guard = PromptGuard(
    detectors=[MyCustomDetector()],
    custom_policy_path="./my_policy.yaml"
)
```

## Policy Use Cases

### Healthcare (HIPAA PHI)

```yaml
name: hipaa_phi
description: HIPAA-compliant Protected Health Information masking
entities:
  PERSON:
    placeholder: "[PATIENT_{i}]"
  EMAIL:
    placeholder: "[CONTACT_{i}]"
  PHONE:
    placeholder: "[PHONE_{i}]"
  SSN:
    placeholder: "[ID_{i}]"
  MRN:  # Medical Record Number
    placeholder: "[MRN_{i}]"
```

### Financial Services

```yaml
name: financial_pii
description: Financial industry PII masking
entities:
  CREDIT_CARD:
    placeholder: "[CARD_{i}]"
  SSN:
    placeholder: "[TAX_ID_{i}]"
  ACCOUNT_NUMBER:
    placeholder: "[ACCT_{i}]"
  ROUTING_NUMBER:
    placeholder: "[ROUTING_{i}]"
```

### Developer/API Tools

```yaml
name: dev_secrets
description: Mask API keys and secrets in developer tools
entities:
  API_KEY:
    placeholder: "[API_KEY_{i}]"
  ACCESS_TOKEN:
    placeholder: "[TOKEN_{i}]"
  PASSWORD:
    placeholder: "[PASS_{i}]"
  IP_ADDRESS:
    placeholder: "[IP_{i}]"
```

### SaaS Analytics

```yaml
name: saas_analytics
description: Anonymize user data for analytics while preserving structure
entities:
  EMAIL:
    placeholder: "[USER_{i}]"
  IP_ADDRESS:
    placeholder: "[SOURCE_{i}]"
  # Keep numeric IDs for analytics correlation
  # but remove personal identifiers
```

## Policy Best Practices

### 1. Start Minimal

Begin with detecting only the PII types you absolutely need to mask:

```yaml
# Good: Focused policy
entities:
  EMAIL:
    placeholder: "[EMAIL_{i}]"
  PHONE:
    placeholder: "[PHONE_{i}]"
```

vs.

```yaml
# Avoid: Over-masking
entities:
  # ... 20 different entity types
```

### 2. Use Descriptive Placeholders

Make placeholders that give context:

```yaml
# Good
EMAIL:
  placeholder: "[EMAIL_{i}]"

# Less clear
EMAIL:
  placeholder: "[E_{i}]"
```

### 3. Consider Token Efficiency (for SLMs)

Shorter placeholders save tokens in models with limited context:

```yaml
# For large models (LLMs)
PERSON:
  placeholder: "[PERSON_NAME_{i}]"  # 5-6 tokens

# For small models (SLMs)
PERSON:
  placeholder: "[USER_{i}]"  # 3-4 tokens
```

### 4. Match Your Compliance Requirements

Different industries have different PII definitions:

- **GDPR**: Names, emails, IPs, location data
- **HIPAA**: + medical record numbers, health data
- **PCI-DSS**: + credit card, CVV, expiration dates
- **CCPA**: + consumer records, purchase history

### 5. Test Your Policy

Use the evaluation framework:

```bash
cd eval/scripts
python evaluate_pii_detection.py
```

## Advanced: Future Policy Features

### Strategy Field

```yaml
entities:
  EMAIL:
    placeholder: "[EMAIL_{i}]"
    strategy: "replace"  # replace | redact | pseudonymize

  SSN:
    strategy: "redact"  # Becomes "***-**-****"

  PERSON:
    strategy: "pseudonymize"  # Becomes realistic fake name
```

### Confidence Thresholds

```yaml
entities:
  PERSON:
    placeholder: "[NAME_{i}]"
    confidence_threshold: 0.8  # Only mask if >80% confident
```

### Conditional Masking

```yaml
entities:
  EMAIL:
    placeholder: "[EMAIL_{i}]"
    mask_if:
      - domain_not_in: ["mycompany.com", "trusted.org"]
```

## Contributing Policies

Have a policy that might be useful to others? Consider contributing it!

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

# llm-slm-prompt-guard (Python)

Python implementation of policy-driven PII anonymization for LLM/SLM applications.

## Installation

```bash
pip install llm-slm-prompt-guard
```

## Quick Start

```python
from prompt_guard import PromptGuard

# Initialize with default settings
guard = PromptGuard(
    detectors=["regex"],
    policy="default_pii"
)

# Anonymize user input
user_prompt = "Hi, I'm John Smith. Email me at john.smith@example.com or call 555-123-4567."
anonymized, mapping = guard.anonymize(user_prompt)

print(anonymized)
# Output: "Hi, I'm [NAME_1]. Email me at [EMAIL_1] or call [PHONE_1]."

# Send anonymized prompt to LLM/SLM...
# llm_response = your_llm_call(anonymized)

# De-anonymize the response
# final_response = guard.deanonymize(llm_response, mapping)
```

## Development

```bash
cd packages/python
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Type check
mypy src/
```

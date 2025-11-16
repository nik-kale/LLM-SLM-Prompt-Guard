# Contributing to llm-slm-prompt-guard

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

Key principles:
- Be respectful and considerate
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards others

---

## Getting Started

### Prerequisites

**Python:**
- Python 3.9 or higher
- pip or poetry

**Node/TypeScript:**
- Node.js 18.x or higher
- npm or yarn

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/llm-slm-prompt-guard.git
   cd llm-slm-prompt-guard
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/nik-kale/llm-slm-prompt-guard.git
   ```

---

## Development Setup

### Python Package

```bash
cd packages/python

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Lint
ruff check src/

# Type check
mypy src/
```

### Node/TypeScript Package

```bash
cd packages/node

# Install dependencies
npm install

# Build
npm run build

# Run tests
npm test

# Lint
npm run lint

# Format
npm run format
```

---

## How to Contribute

### Areas to Contribute

We welcome contributions in these areas:

1. **New Detectors**
   - Integrate existing PII detection libraries
   - Implement custom detection algorithms
   - Add support for new entity types

2. **New Policies**
   - Industry-specific policies (healthcare, finance, etc.)
   - Region-specific policies (GDPR, CCPA, etc.)
   - Custom anonymization strategies

3. **Framework Adapters**
   - LangChain, LlamaIndex, Vercel AI SDK
   - Hugging Face, Ollama, llama.cpp
   - Other LLM/SLM frameworks

4. **Documentation**
   - Tutorials and guides
   - API documentation
   - Examples and use cases

5. **Testing**
   - Unit tests
   - Integration tests
   - Evaluation datasets

6. **Bug Fixes**
   - Fix reported issues
   - Improve error handling
   - Performance optimizations

### Finding Issues to Work On

- Check the [Issues](https://github.com/nik-kale/llm-slm-prompt-guard/issues) page
- Look for issues labeled `good first issue` for beginner-friendly tasks
- Issues labeled `help wanted` are particularly welcome for contributions

---

## Coding Standards

### Python

- **Style**: Follow [PEP 8](https://pep8.org/)
- **Formatter**: Use `black` with default settings
- **Linter**: Use `ruff`
- **Type hints**: Use type hints for all public APIs
- **Docstrings**: Use Google-style docstrings

Example:
```python
def anonymize(self, text: str) -> AnonymizeResult:
    """
    Anonymize PII in the given text.

    Args:
        text: The text to anonymize

    Returns:
        A tuple of (anonymized_text, mapping)

    Raises:
        ValueError: If text is empty
    """
    pass
```

### TypeScript

- **Style**: Follow [TypeScript guidelines](https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html)
- **Formatter**: Use `prettier`
- **Linter**: Use `eslint`
- **Type safety**: Enable `strict` mode
- **Documentation**: Use TSDoc comments

Example:
```typescript
/**
 * Anonymize PII in the given text.
 *
 * @param text - The text to anonymize
 * @returns An object containing anonymized text and mapping
 * @throws {Error} If text is empty
 */
anonymize(text: string): AnonymizeResult {
  // ...
}
```

### General Principles

1. **Keep it simple**: Prefer clarity over cleverness
2. **Write tests**: All new features should have tests
3. **Document public APIs**: All public functions/classes need documentation
4. **Follow existing patterns**: Match the style of existing code
5. **No breaking changes**: Maintain backward compatibility in minor versions

---

## Testing

### Writing Tests

**Python:**
```python
# tests/test_guard.py
import pytest
from prompt_guard import PromptGuard

def test_anonymize_email():
    guard = PromptGuard(policy="default_pii")
    text = "Email me at john@example.com"
    anonymized, mapping = guard.anonymize(text)

    assert "[EMAIL_1]" in anonymized
    assert mapping["[EMAIL_1]"] == "john@example.com"
```

**TypeScript:**
```typescript
// tests/guard.test.ts
import { PromptGuard } from '../src';

describe('PromptGuard', () => {
  it('should anonymize email addresses', () => {
    const guard = new PromptGuard({ policy: 'default_pii' });
    const text = 'Email me at john@example.com';
    const { anonymized, mapping } = guard.anonymize(text);

    expect(anonymized).toContain('[EMAIL_1]');
    expect(mapping['[EMAIL_1]']).toBe('john@example.com');
  });
});
```

### Running Tests

```bash
# Python
cd packages/python
pytest

# Node
cd packages/node
npm test
```

### Test Coverage

- Aim for >80% test coverage
- All new features must include tests
- Bug fixes should include regression tests

---

## Documentation

### Code Documentation

- Document all public APIs
- Include usage examples in docstrings
- Explain non-obvious implementation details

### User Documentation

Located in `docs/`:
- Update relevant docs when adding features
- Add examples for new functionality
- Keep the README up to date

### Examples

When adding new features, consider adding an example in `examples/`:
- Should be runnable out of the box
- Include clear comments
- Add a README explaining the example

---

## Submitting Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-presidio-detector`
- `fix/email-detection-bug`
- `docs/update-readme`
- `test/add-integration-tests`

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

Examples:
```
feat(python): add Presidio detector integration

Integrates Microsoft Presidio for ML-based PII detection.
Adds optional dependency and fallback to regex detector.

Closes #42
```

```
fix(node): correct email regex pattern

The previous pattern failed to match emails with plus signs.
Updated regex to handle all valid email formats.
```

### Pull Request Process

1. **Update your fork**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Write code
   - Add tests
   - Update documentation
   - Run linters and formatters

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**:
   - Go to the main repository on GitHub
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill out the PR template
   - Request review

### PR Guidelines

- **One feature per PR**: Keep PRs focused on a single change
- **Reference issues**: Link to related issues (e.g., "Closes #123")
- **Update CHANGELOG**: Add entry for notable changes (we'll help with this)
- **Pass CI**: Ensure all tests pass
- **Get review**: Wait for maintainer review and address feedback

### Review Process

- PRs require at least one approving review from a maintainer
- Address all review comments
- Keep the PR up to date with main
- Be patient and respectful during review

---

## Additional Guidelines

### Adding a New Detector

1. Create detector class inheriting from `BaseDetector`:
   ```python
   # packages/python/src/prompt_guard/detectors/my_detector.py
   from .base import BaseDetector
   from ..types import DetectorResult

   class MyDetector(BaseDetector):
       def detect(self, text: str) -> List[DetectorResult]:
           # Your detection logic
           return results
   ```

2. Update `__init__.py` to export your detector
3. Add tests in `tests/detectors/test_my_detector.py`
4. Update documentation
5. Add example usage

### Adding a New Policy

1. Create YAML file in `packages/python/src/prompt_guard/policies/`:
   ```yaml
   name: my_policy
   description: My custom policy
   entities:
     EMAIL:
       placeholder: "[EMAIL_{i}]"
   ```

2. Add tests to verify policy loading
3. Document the policy in `docs/policies.md`
4. Add example usage

### Adding a Framework Adapter

1. Create adapter in `packages/python/src/prompt_guard/adapters/`
2. Follow the existing adapter pattern
3. Add comprehensive tests
4. Document in `docs/adapters.md`
5. Add working example in `examples/`

---

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/nik-kale/llm-slm-prompt-guard/discussions)
- **Bugs**: Open an [Issue](https://github.com/nik-kale/llm-slm-prompt-guard/issues)
- **Chat**: Join our community discussions

---

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Acknowledged in the README (for significant contributions)

---

Thank you for contributing to llm-slm-prompt-guard! 🎉

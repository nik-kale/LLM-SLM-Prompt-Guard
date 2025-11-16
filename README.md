# llm-slm-prompt-guard

**Policy-driven PII anonymization & de-anonymization for LLM/SLM apps.**

`llm-slm-prompt-guard` is a lightweight, framework-agnostic layer that sits between your application and any LLM/SLM provider (OpenAI, Anthropic, etc.) and:

- 🔍 **Detects PII** (names, emails, phone numbers, IDs, etc.) in prompts
- 🧼 **Anonymizes** that PII according to a configurable policy
- 🤖 **Sends only sanitized prompts** to LLMs/SLMs
- 🔁 **Optionally de-anonymizes** the response before returning it to the user

Use it as:

- A **Python library** (`PromptGuard`)
- A **Node/TypeScript library**
- A simple **middleware / gateway** you can plug into any LLM/SLM stack

---

## Why this exists

Most LLM/SLM apps do *something* like this:

```text
user enters prompt → app → send directly to LLM/SLM → log prompt + response
```

If that prompt contains:
- customer names
- email addresses
- internal ticket IDs
- access keys
- health or financial data

…you're now in privacy, compliance, and "oh no" territory.

There are great tools like Microsoft Presidio and libraries like anonLLM, but they tend to be:
- 🔸 Single-language or single-backend
- 🔸 Demo scripts rather than a pluggable layer
- 🔸 Hard to drop into frameworks like LangChain, LlamaIndex, Vercel AI SDK

`llm-slm-prompt-guard` aims to be the missing middle:

**A small, composable guardrail that devs can add before any LLM/SLM call to ensure PII never leaves the app in the first place.**

---

## High-level design

```
┌───────────────┐      ┌────────────────┐      ┌────────────────────┐
│   User/App    │  →   │ llm-slm-prompt-│  →   │   LLM/SLM provider │
│   (frontend)  │      │     guard      │      │  (OpenAI, etc.)    │
└───────────────┘      └────────────────┘      └────────────────────┘
                             │
                             │ anonymize(prompt)
                             ↓
                        [ANONYMIZED PROMPT]

# Optional:
LLM/SLM response + mapping → de-anonymize → final response
```

Key ideas:
- **Detectors**: pluggable backends that find PII (regex, Presidio, spaCy, etc.)
- **Policies**: YAML/JSON that define what to mask & how (e.g., default_pii, gdpr_strict, hipaa_phi)
- **Mapping**: mapping table `{ placeholder → original value }` stored in memory or a secure store
- **De-anonymization**: optional stage to reinsert the original values into the LLM's/SLM's response

---

## Python quick start

Install (once published to PyPI):

```bash
pip install llm-slm-prompt-guard
```

Basic usage:

```python
from prompt_guard import PromptGuard

guard = PromptGuard(
    detectors=["regex"],        # in v0.1, a simple regex-based detector
    policy="default_pii",       # maps PII types → placeholders
)

user_prompt = "Hi, I'm John Smith. My email is john.smith@example.com."

anonymized, mapping = guard.anonymize(user_prompt)

# anonymized might look like:
# "Hi, I'm [NAME_1]. My email is [EMAIL_1]."

# Call your LLM/SLM with anonymized prompt
from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": anonymized}]
)

llm_reply = completion.choices[0].message.content

final_reply = guard.deanonymize(llm_reply, mapping)
print(final_reply)
```

---

## Node / TypeScript quick start

Install (once published):

```bash
npm install llm-slm-prompt-guard
# or
yarn add llm-slm-prompt-guard
```

Example Express middleware:

```typescript
import express from "express";
import { createPromptGuard } from "llm-slm-prompt-guard";
import OpenAI from "openai";

const app = express();
app.use(express.json());

const guard = createPromptGuard({
  detectors: ["regex"],
  policy: "default_pii"
});

const client = new OpenAI();

app.post("/chat", async (req, res) => {
  const { prompt } = req.body;

  const { anonymized, mapping } = guard.anonymize(prompt);

  const completion = await client.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: anonymized }]
  });

  const answer = completion.choices[0].message?.content ?? "";
  const finalAnswer = guard.deanonymize(answer, mapping);

  res.json({ answer: finalAnswer });
});

app.listen(3000, () => {
  console.log("Listening on http://localhost:3000");
});
```

---

## Policies

Policies live under `packages/python/src/prompt_guard/policies/` and similar for Node.

Example: `default_pii.yaml`

```yaml
name: default_pii
description: Basic PII masking for names, emails, and phone numbers.
entities:
  PERSON:
    placeholder: "[NAME_{i}]"
  EMAIL:
    placeholder: "[EMAIL_{i}]"
  PHONE:
    placeholder: "[PHONE_{i}]"
```

You can define:
- which entity types to detect (PERSON, EMAIL, PHONE, IP_ADDRESS, etc.)
- which placeholder format to use
- later: whether to mask, drop, or pseudonymize with synthetic but realistic values

See [docs/policies.md](docs/policies.md) for more details.

---

## SLM-Specific Features

Special optimizations for Small Language Models:

### `slm_local` Policy
- **Shorter placeholders** to save tokens (e.g., `[USER_{i}]` instead of `[PERSON_{i}]`)
- **Lightweight detection** with minimal overhead
- **Privacy-first** for on-device/local inference

Example:
```python
guard = PromptGuard(policy="slm_local")
```

### Use Cases
- 📱 Mobile apps with on-device AI
- 🖥️ Edge computing scenarios
- 🔒 Privacy-sensitive applications
- ⚡ Resource-constrained environments

---

## Roadmap (high level)

- ✅ **v0.1** – Python core (PromptGuard), regex detector, default policy
- ⏳ **v0.2** – Node/TS core API and basic Express middleware
- ⏳ **v0.3** – Presidio backend integration (optional dependency)
- ⏳ **v0.4** – LangChain & LlamaIndex adapters
- ⏳ **v0.5** – Evaluation harness (eval/) with PII vs utility metrics
- ⏳ **v0.6** – HTTP proxy mode (drop-in for any LLM client)
- ⏳ **v0.7** – Additional policies (GDPR, HIPAA-like, "anonymous analytics")

See [docs/roadmap.md](docs/roadmap.md) for detailed roadmap.

---

## Documentation

- 📖 [Architecture](docs/architecture.md) - System design and components
- 📋 [Policies](docs/policies.md) - Built-in and custom policies
- 🔌 [Adapters](docs/adapters.md) - Framework integrations
- 🗺️ [Roadmap](docs/roadmap.md) - Future plans and releases

---

## Examples

Check out the [examples/](examples/) directory for complete working examples:

- **Python FastAPI**: [examples/python-fastapi-chat/](examples/python-fastapi-chat/)
- **Node Express**: [examples/node-express-chat/](examples/node-express-chat/)

---

## Contributing

We welcome contributions of all kinds:
- New detector backends (spaCy, Presidio, custom regex packs, cloud APIs)
- New policies (EU-specific, finance-specific, healthcare-specific)
- Framework adapters (Vercel AI SDK, LangChain, LlamaIndex, etc.)
- Eval datasets and metrics for PII vs prompt utility
- Docs, examples, and tutorials

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

---

## License

MIT – use it freely in commercial and open-source projects.

See [LICENSE](LICENSE) for details.

---

## Repository Structure

```
llm-slm-prompt-guard/
├── packages/
│   ├── python/               # Python implementation
│   │   ├── src/prompt_guard/
│   │   └── pyproject.toml
│   └── node/                 # Node/TypeScript implementation
│       ├── src/
│       └── package.json
├── examples/
│   ├── python-fastapi-chat/  # FastAPI example
│   └── node-express-chat/    # Express example
├── eval/
│   ├── datasets/             # Test datasets
│   └── scripts/              # Evaluation scripts
├── docs/                     # Documentation
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── workflows/            # CI/CD
└── README.md
```

---

## Community

- 🐛 [Report a bug](https://github.com/nik-kale/llm-slm-prompt-guard/issues/new?template=bug_report.md)
- 💡 [Request a feature](https://github.com/nik-kale/llm-slm-prompt-guard/issues/new?template=feature_request.md)
- 💬 [Discussions](https://github.com/nik-kale/llm-slm-prompt-guard/discussions)

---

## Star History

If you find this useful, please consider giving it a ⭐ on GitHub!

---

**Built with ❤️ for the LLM/SLM community**

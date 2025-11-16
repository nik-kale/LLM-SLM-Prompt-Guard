# llm-slm-prompt-guard (Node/TypeScript)

Node/TypeScript implementation of policy-driven PII anonymization for LLM/SLM applications.

## Installation

```bash
npm install llm-slm-prompt-guard
# or
yarn add llm-slm-prompt-guard
```

## Quick Start

```typescript
import { PromptGuard } from "llm-slm-prompt-guard";

// Initialize with default settings
const guard = new PromptGuard({
  detectors: ["regex"],
  policy: "default_pii"
});

// Anonymize user input
const userPrompt = "Hi, I'm John Smith. Email me at john.smith@example.com or call 555-123-4567.";
const { anonymized, mapping } = guard.anonymize(userPrompt);

console.log(anonymized);
// Output: "Hi, I'm [NAME_1]. Email me at [EMAIL_1] or call [PHONE_1]."

// Send anonymized prompt to LLM/SLM...
// const llmResponse = await yourLLMCall(anonymized);

// De-anonymize the response
// const finalResponse = guard.deanonymize(llmResponse, mapping);
```

## Express Middleware Example

```typescript
import express from "express";
import { createPromptGuard } from "llm-slm-prompt-guard";

const app = express();
const guard = createPromptGuard({ policy: "default_pii" });

app.post("/chat", async (req, res) => {
  const { anonymized, mapping } = guard.anonymize(req.body.prompt);

  // Call your LLM/SLM...
  const llmResponse = await yourLLMCall(anonymized);

  // De-anonymize and return
  const finalResponse = guard.deanonymize(llmResponse, mapping);
  res.json({ response: finalResponse });
});
```

## Development

```bash
cd packages/node
npm install

# Build
npm run build

# Test
npm test

# Lint
npm run lint
```

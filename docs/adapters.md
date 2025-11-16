# Framework Adapters

This guide shows how to integrate `llm-slm-prompt-guard` with popular LLM/SLM frameworks and platforms.

## Table of Contents

- [Direct LLM API Integration](#direct-llm-api-integration)
- [LangChain (Planned)](#langchain-planned)
- [LlamaIndex (Planned)](#llamaindex-planned)
- [Vercel AI SDK (Planned)](#vercel-ai-sdk-planned)
- [Local Models (Ollama, llama.cpp)](#local-models)
- [Custom Integration](#custom-integration)

---

## Direct LLM API Integration

### OpenAI (Python)

```python
from openai import OpenAI
from prompt_guard import PromptGuard

client = OpenAI()
guard = PromptGuard(policy="default_pii")

def chat(user_message: str) -> str:
    # Anonymize
    anonymized, mapping = guard.anonymize(user_message)

    # Call OpenAI
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": anonymized}
        ]
    )

    # De-anonymize
    answer = response.choices[0].message.content
    return guard.deanonymize(answer, mapping)

# Usage
print(chat("Hi, I'm John Smith at john@example.com"))
```

### OpenAI (Node/TypeScript)

```typescript
import OpenAI from "openai";
import { PromptGuard } from "llm-slm-prompt-guard";

const client = new OpenAI();
const guard = new PromptGuard({ policy: "default_pii" });

async function chat(userMessage: string): Promise<string> {
  // Anonymize
  const { anonymized, mapping } = guard.anonymize(userMessage);

  // Call OpenAI
  const response = await client.chat.completions.create({
    model: "gpt-4o",
    messages: [
      { role: "user", content: anonymized }
    ]
  });

  // De-anonymize
  const answer = response.choices[0].message?.content ?? "";
  return guard.deanonymize(answer, mapping);
}

// Usage
chat("Hi, I'm John Smith at john@example.com").then(console.log);
```

### Anthropic Claude

```python
from anthropic import Anthropic
from prompt_guard import PromptGuard

client = Anthropic()
guard = PromptGuard(policy="default_pii")

def chat(user_message: str) -> str:
    anonymized, mapping = guard.anonymize(user_message)

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": anonymized}
        ]
    )

    answer = message.content[0].text
    return guard.deanonymize(answer, mapping)
```

### Google Gemini

```python
import google.generativeai as genai
from prompt_guard import PromptGuard

genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel('gemini-pro')
guard = PromptGuard(policy="default_pii")

def chat(user_message: str) -> str:
    anonymized, mapping = guard.anonymize(user_message)
    response = model.generate_content(anonymized)
    return guard.deanonymize(response.text, mapping)
```

---

## LangChain (Planned)

**Status**: Coming in v0.2

### Python

```python
from langchain.llms import OpenAI
from prompt_guard.adapters import LangChainGuard

# Wrap any LangChain LLM
llm = LangChainGuard(
    llm=OpenAI(),
    policy="default_pii",
    deanonymize=True  # Auto de-anonymize responses
)

# Use normally
response = llm("Hi, I'm John at john@example.com")
# PII is automatically masked before sending to LLM
```

### TypeScript

```typescript
import { OpenAI } from "langchain/llms/openai";
import { LangChainGuard } from "llm-slm-prompt-guard/adapters/langchain";

const llm = new LangChainGuard({
  llm: new OpenAI(),
  policy: "default_pii",
  deanonymize: true
});

const response = await llm.call("Hi, I'm John at john@example.com");
```

### With Chains

```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from prompt_guard.adapters import LangChainGuard

template = "You are a helpful assistant. User says: {user_input}"
prompt = PromptTemplate(template=template, input_variables=["user_input"])

llm = LangChainGuard(llm=OpenAI(), policy="default_pii")
chain = LLMChain(llm=llm, prompt=prompt)

# PII in user_input is automatically protected
result = chain.run(user_input="My email is john@example.com")
```

---

## LlamaIndex (Planned)

**Status**: Coming in v0.2

### Python

```python
from llama_index import VectorStoreIndex, SimpleDirectoryReader
from prompt_guard.adapters import LlamaIndexGuard

documents = SimpleDirectoryReader('data').load_data()
index = VectorStoreIndex.from_documents(documents)

# Wrap the query engine
query_engine = LlamaIndexGuard(
    query_engine=index.as_query_engine(),
    policy="default_pii"
)

# Queries are automatically anonymized
response = query_engine.query("What's the email for John Smith?")
```

### TypeScript

```typescript
import { VectorStoreIndex } from "llamaindex";
import { LlamaIndexGuard } from "llm-slm-prompt-guard/adapters/llamaindex";

const index = await VectorStoreIndex.fromDocuments(documents);

const queryEngine = new LlamaIndexGuard({
  queryEngine: index.asQueryEngine(),
  policy: "default_pii"
});

const response = await queryEngine.query("What's John's email?");
```

---

## Vercel AI SDK (Planned)

**Status**: Coming in v0.5

### Streaming with Edge Functions

```typescript
import { OpenAIStream, StreamingTextResponse } from 'ai';
import { PromptGuardStream } from 'llm-slm-prompt-guard/vercel';
import OpenAI from 'openai';

const openai = new OpenAI();

export async function POST(req: Request) {
  const { messages } = await req.json();

  // Create guard stream
  const guardStream = new PromptGuardStream({ policy: 'default_pii' });

  // Anonymize last message
  const guardedMessages = guardStream.anonymizeMessages(messages);

  const response = await openai.chat.completions.create({
    model: 'gpt-4o',
    stream: true,
    messages: guardedMessages,
  });

  // De-anonymize streaming response
  const stream = OpenAIStream(response);
  const protectedStream = guardStream.deanonymizeStream(stream);

  return new StreamingTextResponse(protectedStream);
}
```

---

## Local Models

### Ollama (Python)

```python
import ollama
from prompt_guard import PromptGuard

guard = PromptGuard(policy="slm_local")  # Use SLM-optimized policy

def chat(message: str) -> str:
    anonymized, mapping = guard.anonymize(message)

    response = ollama.chat(
        model='llama2',
        messages=[{'role': 'user', 'content': anonymized}]
    )

    return guard.deanonymize(response['message']['content'], mapping)

# Usage
print(chat("My email is john@example.com"))
```

### Ollama (Node/TypeScript)

```typescript
import ollama from 'ollama';
import { PromptGuard } from 'llm-slm-prompt-guard';

const guard = new PromptGuard({ policy: 'slm_local' });

async function chat(message: string): Promise<string> {
  const { anonymized, mapping } = guard.anonymize(message);

  const response = await ollama.chat({
    model: 'llama2',
    messages: [{ role: 'user', content: anonymized }]
  });

  return guard.deanonymize(response.message.content, mapping);
}
```

### llama.cpp (Python)

```python
from llama_cpp import Llama
from prompt_guard import PromptGuard

llm = Llama(model_path="./models/llama-2-7b.gguf")
guard = PromptGuard(policy="slm_local")

def chat(message: str) -> str:
    anonymized, mapping = guard.anonymize(message)

    output = llm(
        anonymized,
        max_tokens=256,
        temperature=0.7
    )

    return guard.deanonymize(output['choices'][0]['text'], mapping)
```

### Hugging Face Transformers

```python
from transformers import pipeline
from prompt_guard import PromptGuard

generator = pipeline('text-generation', model='gpt2')
guard = PromptGuard(policy="slm_local")

def generate(prompt: str) -> str:
    anonymized, mapping = guard.anonymize(prompt)
    output = generator(anonymized, max_length=100)[0]['generated_text']
    return guard.deanonymize(output, mapping)
```

---

## Custom Integration

### Creating a Wrapper Class

```python
from typing import Any
from prompt_guard import PromptGuard

class ProtectedLLM:
    """Generic wrapper for any LLM client."""

    def __init__(self, client: Any, policy: str = "default_pii"):
        self.client = client
        self.guard = PromptGuard(policy=policy)

    def chat(self, message: str, **kwargs) -> str:
        # Anonymize
        anonymized, mapping = self.guard.anonymize(message)

        # Call the underlying LLM
        response = self.client.chat(anonymized, **kwargs)

        # De-anonymize
        return self.guard.deanonymize(response, mapping)

# Usage with any client
from my_llm_library import Client

protected_llm = ProtectedLLM(Client(), policy="default_pii")
result = protected_llm.chat("My email is john@example.com")
```

### Middleware Pattern (Express)

```typescript
import express from 'express';
import { PromptGuard } from 'llm-slm-prompt-guard';

const guard = new PromptGuard({ policy: 'default_pii' });

// Middleware to anonymize request bodies
function piiProtection(req: express.Request, res: express.Response, next: express.NextFunction) {
  if (req.body.prompt) {
    const { anonymized, mapping } = guard.anonymize(req.body.prompt);
    req.body.originalPrompt = req.body.prompt;
    req.body.prompt = anonymized;
    req.body.piiMapping = mapping;
  }
  next();
}

// Use in routes
app.post('/chat', piiProtection, async (req, res) => {
  const llmResponse = await callLLM(req.body.prompt);
  const finalResponse = guard.deanonymize(llmResponse, req.body.piiMapping);
  res.json({ response: finalResponse });
});
```

### FastAPI Dependency

```python
from fastapi import FastAPI, Depends
from prompt_guard import PromptGuard

app = FastAPI()

def get_guard():
    return PromptGuard(policy="default_pii")

@app.post("/chat")
async def chat(
    prompt: str,
    guard: PromptGuard = Depends(get_guard)
):
    anonymized, mapping = guard.anonymize(prompt)
    llm_response = await call_llm(anonymized)
    return {"response": guard.deanonymize(llm_response, mapping)}
```

---

## Streaming Support (Future)

### Async/Await Pattern

```python
import asyncio
from prompt_guard import AsyncPromptGuard

guard = AsyncPromptGuard(policy="default_pii")

async def chat_stream(message: str):
    anonymized, mapping = await guard.anonymize_async(message)

    async for chunk in llm.stream(anonymized):
        deanonymized_chunk = await guard.deanonymize_async(chunk, mapping)
        yield deanonymized_chunk
```

### Server-Sent Events (SSE)

```typescript
import { PromptGuard } from 'llm-slm-prompt-guard';

const guard = new PromptGuard({ policy: 'default_pii' });

app.get('/stream', async (req, res) => {
  const { anonymized, mapping } = guard.anonymize(req.query.prompt);

  res.setHeader('Content-Type', 'text/event-stream');

  for await (const chunk of streamFromLLM(anonymized)) {
    const deanonymized = guard.deanonymize(chunk, mapping);
    res.write(`data: ${deanonymized}\n\n`);
  }

  res.end();
});
```

---

## Best Practices

### 1. Choose the Right Policy

```python
# For general use
guard = PromptGuard(policy="default_pii")

# For on-device/local SLMs
guard = PromptGuard(policy="slm_local")

# For GDPR compliance
guard = PromptGuard(policy="gdpr_strict")
```

### 2. Persistent Mapping for Multi-Turn Conversations

```python
# Store mapping in session or database
session['pii_mapping'] = mapping

# Reuse across turns
combined_mapping = {**session.get('pii_mapping', {}), **new_mapping}
```

### 3. Error Handling

```python
try:
    anonymized, mapping = guard.anonymize(user_input)
    response = llm.chat(anonymized)
    return guard.deanonymize(response, mapping)
except Exception as e:
    logger.error(f"PII protection failed: {e}")
    # Fallback: either reject the request or proceed without protection
    raise
```

### 4. Testing

```python
# Test with sample PII
test_cases = [
    "My email is test@example.com",
    "Call me at 555-123-4567",
    "I'm John Smith"
]

for test in test_cases:
    anonymized, mapping = guard.anonymize(test)
    print(f"Original:    {test}")
    print(f"Anonymized:  {anonymized}")
    print(f"Mapping:     {mapping}")
    print()
```

---

## Contributing Adapters

Have an adapter for a framework not listed here? We'd love to include it!

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on:
- Code style
- Testing requirements
- Documentation standards
- Submitting pull requests

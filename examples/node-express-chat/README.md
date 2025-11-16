# Express Chat Example

This example demonstrates how to integrate `llm-slm-prompt-guard` with an Express application to anonymize PII in chat prompts before sending them to an LLM/SLM.

## Setup

```bash
# Install dependencies
npm install

# Build the package (if not already built)
cd ../../packages/node
npm install
npm run build
cd ../../examples/node-express-chat
```

## Run

```bash
# Development mode with auto-reload
npm run dev

# Or build and run
npm run build
npm start
```

The API will be available at `http://localhost:3000`.

## Example Usage

### Test anonymization only

```bash
curl -X POST http://localhost:3000/anonymize \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hi, I am John Smith. My email is john@example.com and my phone is 555-123-4567."
  }'
```

Response:
```json
{
  "original": "Hi, I am John Smith. My email is john@example.com and my phone is 555-123-4567.",
  "anonymized": "Hi, I am [NAME_1]. My email is [EMAIL_1] and my phone is [PHONE_1].",
  "mapping": {
    "[NAME_1]": "John Smith",
    "[EMAIL_1]": "john@example.com",
    "[PHONE_1]": "555-123-4567"
  },
  "piiDetected": 3
}
```

### Chat with mock LLM

```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "My name is Jane Doe and I need help with my account jane.doe@example.com",
    "useMock": true
  }'
```

### Chat with real LLM

1. Set your OpenAI API key: `export OPENAI_API_KEY=your-key-here`
2. Uncomment the OpenAI integration in `server.ts`
3. Install OpenAI: `npm install openai`
4. Make a request with `useMock: false`

```bash
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "My name is Jane Doe and I need help",
    "model": "gpt-4o-mini",
    "useMock": false
  }'
```

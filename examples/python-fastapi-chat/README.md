# FastAPI Chat Example

This example demonstrates how to integrate `llm-slm-prompt-guard` with a FastAPI application to anonymize PII in chat prompts before sending them to an LLM/SLM.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install the prompt-guard package (from local)
pip install -e ../../packages/python
```

## Run

```bash
python main.py
```

The API will be available at `http://localhost:8000`.

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Usage

### Test anonymization only

```bash
curl -X POST http://localhost:8000/anonymize \
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
  "pii_detected": 3
}
```

### Chat with mock LLM

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "My name is Jane Doe and I need help with my account jane.doe@example.com",
    "use_mock": true
  }'
```

### Chat with real LLM

1. Set your OpenAI API key: `export OPENAI_API_KEY=your-key-here`
2. Uncomment the OpenAI integration in `main.py`
3. Make a request with `use_mock: false`

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "My name is Jane Doe and I need help",
    "model": "gpt-4o-mini",
    "use_mock": false
  }'
```

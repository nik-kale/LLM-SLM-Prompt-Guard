# Ollama Local SLM Example

This example demonstrates using `llm-slm-prompt-guard` with Ollama for privacy-preserving local LLM/SLM inference.

## Why This Matters

When running language models locally (on-device or on-premises), PII protection is still important:
- **Logging**: Anonymized logs can be safely stored or shared
- **Analytics**: Track usage patterns without exposing personal data
- **Development**: Test and debug without handling real PII
- **Compliance**: Meet data protection requirements even for local processing

## Prerequisites

### 1. Install Ollama

Download and install Ollama from [https://ollama.ai/](https://ollama.ai/)

### 2. Pull a Model

```bash
# Recommended for this demo (fast and capable)
ollama pull llama2

# Or try other models:
ollama pull mistral
ollama pull phi
ollama pull gemma
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt

# Install prompt-guard package (from local)
pip install -e ../../packages/python
```

## Running the Examples

### Interactive Chat Demo

Chat with a local SLM while automatically protecting any PII you enter:

```bash
python main.py --mode interactive
```

Example session:
```
You: Hi, I'm John Smith and my email is john.smith@example.com
[PII Protected: 2 items]
[Anonymized: Hi, I'm [USER_1] and my email is [EMAIL_1]]
Assistant: Hello! How can I help you today?

You: Can you schedule a meeting with sarah@company.com?
[PII Protected: 1 items]
[Anonymized: Can you schedule a meeting with [EMAIL_1]?]
Assistant: I'd be happy to help schedule a meeting...
```

### Batch Processing Demo

See how multiple messages are anonymized in batch:

```bash
python main.py --mode batch
```

Output:
```
1. Original:   Contact me at alice@example.com
   Anonymized: Contact me at [EMAIL_1]
   PII Found:  1 item(s)
     [EMAIL_1] = alice@example.com

2. Original:   My SSN is 123-45-6789
   Anonymized: My SSN is [SSN_1]
   PII Found:  1 item(s)
     [SSN_1] = 123-45-6789
...
```

### Performance Benchmark

Measure the overhead of PII detection for SLM use cases:

```bash
python main.py --mode performance
```

Expected output:
```
Iterations: 1000
Total time: 450.23ms
Average time per anonymization: 0.450ms

✓ Fast enough for real-time SLM inference!
✓ Overhead is negligible compared to SLM inference time (~50-200ms)
```

## How It Works

### 1. Initialization

```python
from prompt_guard import PromptGuard

guard = PromptGuard(
    detectors=["regex"],    # Lightweight, no ML overhead
    policy="slm_local"      # SLM-optimized placeholders
)
```

### 2. Anonymize Before Sending to SLM

```python
user_message = "Email me at john@example.com"

# Detect and anonymize PII
anonymized, mapping = guard.anonymize(user_message)
# anonymized = "Email me at [EMAIL_1]"
# mapping = {"[EMAIL_1]": "john@example.com"}
```

### 3. Send Anonymized Text to Local SLM

```python
import ollama

response = ollama.chat(
    model="llama2",
    messages=[{"role": "user", "content": anonymized}]
)

llm_response = response['message']['content']
```

### 4. De-anonymize Response (Optional)

```python
final_response = guard.deanonymize(llm_response, mapping)
# Restores any PII that the SLM echoed back
```

## Key Features for SLMs

### 1. Minimal Overhead

- **Regex-only detection**: No ML models to load
- **<1ms latency**: Negligible compared to SLM inference
- **Low memory**: <10MB footprint

### 2. Token-Efficient Placeholders

The `slm_local` policy uses shorter placeholders to save tokens:

| Standard | SLM-Optimized | Token Savings |
|----------|---------------|---------------|
| `[PERSON_NAME_1]` | `[USER_1]` | ~60% |
| `[EMAIL_ADDRESS_1]` | `[EMAIL_1]` | ~40% |
| `[IP_ADDRESS_1]` | `[ADDR_1]` | ~50% |

This is critical for SLMs with limited context windows (2k-8k tokens).

### 3. Privacy-First

- **No external APIs**: Everything runs locally
- **No data leaves device**: PII never sent to cloud
- **Offline capable**: Works without internet

### 4. Multi-Turn Conversation Support

The example maintains a persistent PII mapping across conversation turns:

```python
chat = PrivateLocalChat()

# Turn 1
chat.chat("My email is john@example.com")
# Mapping: {[EMAIL_1]: "john@example.com"}

# Turn 2
chat.chat("Please send it to that email")
# SLM can reference [EMAIL_1] consistently
```

## Use Cases

### Personal Assistant

Run a local AI assistant that helps with emails and scheduling:

```python
chat = PrivateLocalChat(model="llama2", policy="slm_local")

result = chat.chat("""
Schedule a meeting with Sarah (sarah@company.com)
and John (john@company.com) for tomorrow at 2 PM.
Send calendar invites to both.
""")

# PII is protected before sending to local SLM
# Logs contain anonymized version only
```

### Customer Support (On-Premises)

Deploy on company servers for customer support:

```python
# All PII is masked before sending to local SLM
# Logs can be safely stored for training/analysis
chat.chat("My account email is customer@example.com and my order ID is ORD-12345")
```

### Healthcare (HIPAA)

Run locally in clinic for patient triage:

```python
# Use custom HIPAA policy
guard = PromptGuard(policy="hipaa_phi")

# Patient data is masked before local SLM processing
result = chat.chat("""
Patient: Jane Doe
DOB: 1985-03-15
Complaint: fever and cough
""")
```

## Supported Models

This example works with any Ollama model:

### Recommended for Local Use

- **llama2** (7B): Good balance of speed and quality
- **mistral** (7B): Fast and capable
- **phi** (2.7B): Very fast, runs on CPU
- **gemma** (2B/7B): Efficient and accurate

### Larger Models (if you have GPU)

- **llama2:13b**: Better quality, slower
- **mixtral**: High quality, requires more RAM

## Performance Tips

### 1. Choose the Right Model

Smaller models are faster but less capable:

```bash
# Fastest (good for simple tasks)
ollama pull phi

# Balanced (recommended)
ollama pull llama2

# Highest quality (slower)
ollama pull llama2:13b
```

### 2. Use GPU Acceleration

Ollama automatically uses GPU if available. Check with:

```bash
ollama ps
```

### 3. Adjust Context Length

For SLMs, shorter context = faster inference:

```python
response = ollama.chat(
    model="llama2",
    messages=[...],
    options={
        "num_ctx": 2048  # Reduce context window
    }
)
```

### 4. Batch Similar Queries

Group similar queries to avoid repeated model loading:

```python
queries = [query1, query2, query3]
for query in queries:
    result = chat.chat(query)
```

## Troubleshooting

### "Ollama not running"

Start Ollama:
```bash
ollama serve
```

### "Model not found"

Pull the model first:
```bash
ollama pull llama2
```

### "Import Error: No module named 'ollama'"

Install the Ollama Python library:
```bash
pip install ollama
```

### Slow Performance

1. Check if GPU is being used: `ollama ps`
2. Use a smaller model: `ollama pull phi`
3. Reduce context length in the code

## Next Steps

- Try different policies (default_pii, gdpr_strict)
- Add custom detectors for your specific PII types
- Integrate with your own local SLM setup
- Build a complete application with persistent storage

## Learn More

- [Ollama Documentation](https://github.com/ollama/ollama)
- [SLM Use Cases](../../docs/slm-use-cases.md)
- [Policy Configuration](../../docs/policies.md)

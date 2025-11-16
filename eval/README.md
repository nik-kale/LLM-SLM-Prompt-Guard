# Evaluation Framework

This directory contains evaluation scripts and datasets for measuring the performance of `llm-slm-prompt-guard`.

## Structure

```
eval/
├── datasets/           # Labeled test datasets
│   └── sample_prompts.jsonl
├── scripts/            # Evaluation scripts
│   ├── evaluate_pii_detection.py
│   └── evaluate_pii_vs_utility.py
└── results/            # Output directory for results (auto-created)
```

## Datasets

### sample_prompts.jsonl

A labeled dataset of prompts with expected PII types. Each line contains:
- `id`: Unique identifier
- `text`: The prompt text
- `expected_pii`: List of PII types that should be detected
- `category`: Category of the prompt (basic, contact, sensitive, etc.)

## Evaluation Scripts

### 1. PII Detection Quality

Evaluates how accurately the guard detects PII:

```bash
cd eval/scripts
python evaluate_pii_detection.py
```

**Metrics:**
- **Precision**: Of all PII detected, how many were actually PII?
- **Recall**: Of all actual PII, how many did we detect?
- **F1 Score**: Harmonic mean of precision and recall

### 2. PII vs Utility Trade-off

Evaluates how much anonymization affects prompt utility:

```bash
cd eval/scripts
python evaluate_pii_vs_utility.py
```

**Metrics:**
- **Character Preservation Ratio**: Percentage of characters preserved
- **Word Preservation Ratio**: Percentage of words preserved
- **PII Removal Rate**: Number of PII instances removed

## Results

Results are saved in JSON format to `eval/results/`:
- `evaluation_results.json` - PII detection metrics
- `utility_evaluation.json` - Utility preservation metrics

## Adding New Datasets

To add a new evaluation dataset:

1. Create a JSONL file in `datasets/`
2. Each line should be a JSON object with at minimum:
   ```json
   {
     "id": 1,
     "text": "Your prompt text here",
     "expected_pii": ["EMAIL", "PERSON"],
     "category": "your_category"
   }
   ```
3. Update the evaluation scripts to point to your new dataset

## Future Enhancements

- [ ] Semantic similarity metrics (using embeddings)
- [ ] LLM-based evaluation of response quality
- [ ] Performance benchmarks (latency, throughput)
- [ ] Cross-language evaluation
- [ ] False positive/negative analysis tools

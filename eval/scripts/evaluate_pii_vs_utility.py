"""
Evaluation script for PII vs Utility trade-off.

This script measures how much anonymization affects prompt utility,
using metrics like:
- Character preservation ratio
- Word preservation ratio
- Semantic similarity (if available)
- PII removal rate
"""

import json
import sys
import os
from typing import List, Dict, Tuple

# Add package to path for local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../packages/python/src"))

from prompt_guard import PromptGuard


def load_dataset(filepath: str) -> List[Dict]:
    """Load JSONL dataset."""
    data = []
    with open(filepath, "r") as f:
        for line in f:
            data.append(json.loads(line))
    return data


def calculate_preservation_metrics(original: str, anonymized: str) -> Dict:
    """
    Calculate how much of the original text is preserved.
    """
    orig_chars = len(original)
    anon_chars = len(anonymized)
    orig_words = len(original.split())
    anon_words = len(anonymized.split())

    return {
        "original_chars": orig_chars,
        "anonymized_chars": anon_chars,
        "char_preservation_ratio": anon_chars / orig_chars if orig_chars > 0 else 0,
        "original_words": orig_words,
        "anonymized_words": anon_words,
        "word_preservation_ratio": anon_words / orig_words if orig_words > 0 else 0,
    }


def evaluate_utility(guard: PromptGuard, dataset: List[Dict]) -> Dict:
    """
    Evaluate the utility preservation of anonymization.
    """
    results = {
        "total_samples": len(dataset),
        "avg_char_preservation": 0.0,
        "avg_word_preservation": 0.0,
        "avg_pii_count": 0.0,
        "total_pii_removed": 0,
        "samples": [],
    }

    total_char_preservation = 0.0
    total_word_preservation = 0.0
    total_pii = 0

    for sample in dataset:
        text = sample["text"]

        # Anonymize
        anonymized, mapping = guard.anonymize(text)

        # Calculate metrics
        metrics = calculate_preservation_metrics(text, anonymized)
        pii_count = len(mapping)

        total_char_preservation += metrics["char_preservation_ratio"]
        total_word_preservation += metrics["word_preservation_ratio"]
        total_pii += pii_count

        sample_result = {
            "id": sample.get("id"),
            "category": sample.get("category", "unknown"),
            "original": text,
            "anonymized": anonymized,
            "pii_removed": pii_count,
            "pii_types": list(set(k.split("_")[0][1:] for k in mapping.keys())),
            **metrics,
        }

        results["samples"].append(sample_result)

    # Calculate averages
    n = len(dataset)
    results["avg_char_preservation"] = total_char_preservation / n if n > 0 else 0
    results["avg_word_preservation"] = total_word_preservation / n if n > 0 else 0
    results["avg_pii_count"] = total_pii / n if n > 0 else 0
    results["total_pii_removed"] = total_pii

    return results


def print_results(results: Dict):
    """Pretty print evaluation results."""
    print("\n" + "=" * 60)
    print("PII vs Utility Evaluation Results")
    print("=" * 60)
    print(f"\nUtility Metrics:")
    print(f"  Average Character Preservation: {results['avg_char_preservation']:.2%}")
    print(f"  Average Word Preservation:      {results['avg_word_preservation']:.2%}")
    print(f"\nPII Removal:")
    print(f"  Total PII Instances Removed: {results['total_pii_removed']}")
    print(f"  Average PII per Sample:      {results['avg_pii_count']:.2f}")

    print(f"\nSample Anonymizations:")
    for sample in results["samples"][:5]:  # Show first 5
        print(f"\n  [{sample['id']}] {sample['category']}")
        print(f"  Original:    {sample['original']}")
        print(f"  Anonymized:  {sample['anonymized']}")
        print(f"  PII Removed: {sample['pii_removed']} ({', '.join(sample['pii_types'])})")

    print("\n" + "=" * 60 + "\n")


def main():
    # Initialize guard
    guard = PromptGuard(detectors=["regex"], policy="default_pii")

    # Load dataset
    dataset_path = os.path.join(
        os.path.dirname(__file__), "../datasets/sample_prompts.jsonl"
    )
    dataset = load_dataset(dataset_path)

    print(f"Loaded {len(dataset)} samples from dataset")

    # Evaluate
    results = evaluate_utility(guard, dataset)

    # Print results
    print_results(results)

    # Save detailed results
    output_path = os.path.join(
        os.path.dirname(__file__), "../results/utility_evaluation.json"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Detailed results saved to: {output_path}")


if __name__ == "__main__":
    main()

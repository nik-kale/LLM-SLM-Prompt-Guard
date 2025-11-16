"""
Evaluation script for PII detection quality.

This script evaluates the prompt guard's ability to detect PII
by comparing against a labeled dataset.

Metrics:
- Precision: Of all PII detected, how many were actually PII?
- Recall: Of all actual PII, how many did we detect?
- F1 Score: Harmonic mean of precision and recall
"""

import json
import sys
import os
from typing import List, Dict, Set
from collections import defaultdict

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


def evaluate_detection(guard: PromptGuard, dataset: List[Dict]) -> Dict:
    """
    Evaluate PII detection performance.

    Returns:
        Dictionary with precision, recall, F1, and detailed results
    """
    results = {
        "total_samples": len(dataset),
        "correct_detections": 0,
        "false_positives": 0,
        "false_negatives": 0,
        "by_category": defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0}),
        "details": [],
    }

    for sample in dataset:
        text = sample["text"]
        expected_types = set(sample.get("expected_pii", []))
        category = sample.get("category", "unknown")

        # Anonymize and get detected types
        _, mapping = guard.anonymize(text)
        detected_types = set()
        for placeholder in mapping.keys():
            # Extract entity type from placeholder like "[EMAIL_1]"
            entity_type = placeholder.split("_")[0][1:]  # Remove leading "["
            detected_types.add(entity_type)

        # Calculate metrics
        true_positives = expected_types & detected_types
        false_positives = detected_types - expected_types
        false_negatives = expected_types - detected_types

        # Update overall counts
        results["correct_detections"] += len(true_positives)
        results["false_positives"] += len(false_positives)
        results["false_negatives"] += len(false_negatives)

        # Update category counts
        results["by_category"][category]["tp"] += len(true_positives)
        results["by_category"][category]["fp"] += len(false_positives)
        results["by_category"][category]["fn"] += len(false_negatives)

        # Store details
        results["details"].append(
            {
                "id": sample.get("id"),
                "category": category,
                "expected": list(expected_types),
                "detected": list(detected_types),
                "true_positives": list(true_positives),
                "false_positives": list(false_positives),
                "false_negatives": list(false_negatives),
            }
        )

    # Calculate overall metrics
    tp = results["correct_detections"]
    fp = results["false_positives"]
    fn = results["false_negatives"]

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    results["precision"] = precision
    results["recall"] = recall
    results["f1_score"] = f1

    return results


def print_results(results: Dict):
    """Pretty print evaluation results."""
    print("\n" + "=" * 60)
    print("PII Detection Evaluation Results")
    print("=" * 60)
    print(f"\nOverall Metrics:")
    print(f"  Precision: {results['precision']:.2%}")
    print(f"  Recall:    {results['recall']:.2%}")
    print(f"  F1 Score:  {results['f1_score']:.2%}")
    print(f"\nDetection Counts:")
    print(f"  True Positives:  {results['correct_detections']}")
    print(f"  False Positives: {results['false_positives']}")
    print(f"  False Negatives: {results['false_negatives']}")

    print(f"\nResults by Category:")
    for category, metrics in results["by_category"].items():
        tp = metrics["tp"]
        fp = metrics["fp"]
        fn = metrics["fn"]
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0
        print(f"  {category:12s}: P={prec:.2%}, R={rec:.2%}, F1={f1:.2%}")

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
    results = evaluate_detection(guard, dataset)

    # Print results
    print_results(results)

    # Optionally save detailed results
    output_path = os.path.join(os.path.dirname(__file__), "../results/evaluation_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Detailed results saved to: {output_path}")


if __name__ == "__main__":
    main()

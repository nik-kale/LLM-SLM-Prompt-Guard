"""
Example: Using spaCy-based ML detector for PII detection.

This example demonstrates how to use the SpacyDetector for more accurate
ML-based PII detection compared to regex patterns.

Installation:
    pip install llm-slm-prompt-guard[spacy]
    python -m spacy download en_core_web_sm

Usage:
    python examples/spacy_detector_example.py
"""

from prompt_guard import PromptGuard

# Check if spaCy is available
try:
    from prompt_guard import SpacyDetector
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("❌ spaCy not installed. Install with: pip install llm-slm-prompt-guard[spacy]")
    print("   Then download model: python -m spacy download en_core_web_sm")
    exit(1)


def main():
    print("=== spaCy Detector Example ===\n")

    # Example 1: Basic usage with spaCy detector
    print("Example 1: Basic spaCy Detection")
    print("-" * 50)

    guard = PromptGuard(
        detectors=["spacy"],  # Use spaCy detector
        policy="default_pii"
    )

    text = """
    Hi, I'm Dr. Sarah Johnson from Boston Medical Center.
    You can reach me at sarah.johnson@hospital.com or call 617-555-1234.
    My patient John Smith needs a follow-up appointment.
    """

    anonymized, mapping = guard.anonymize(text)

    print(f"Original:\n{text}")
    print(f"\nAnonymized:\n{anonymized}")
    print(f"\nMapping:\n{mapping}")

    # Example 2: Combining spaCy with regex for comprehensive detection
    print("\n\nExample 2: Combining spaCy + Regex")
    print("-" * 50)

    guard_combined = PromptGuard(
        detectors=["spacy", "enhanced_regex"],  # Combine both
        policy="default_pii"
    )

    text2 = """
    Our company, Acme Corp, is located at 123 Main Street, New York, NY.
    Contact our CEO, Robert Williams, at robert@acme.com.
    Credit card for payment: 4532-1234-5678-9010
    SSN: 123-45-6789
    """

    anonymized2, mapping2 = guard_combined.anonymize(text2)

    print(f"Original:\n{text2}")
    print(f"\nAnonymized:\n{anonymized2}")
    print(f"\nDetected entities:\n{list(mapping2.keys())}")

    # Example 3: Custom confidence threshold
    print("\n\nExample 3: Custom Confidence Threshold")
    print("-" * 50)

    from prompt_guard.detectors.spacy_detector import SpacyDetector

    # Only detect high-confidence entities (>= 0.8)
    spacy_detector = SpacyDetector(
        confidence_threshold=0.8,
        entities=["PERSON", "ORG", "GPE"]  # Only these entity types
    )

    guard_custom = PromptGuard(
        detectors=[spacy_detector],
        policy="default_pii"
    )

    text3 = "Apple announced a new product. Tim Cook presented it in California."

    anonymized3, mapping3 = guard_custom.anonymize(text3)

    print(f"Original:\n{text3}")
    print(f"\nAnonymized:\n{anonymized3}")
    print(f"\nMapping:\n{mapping3}")

    # Example 4: Multi-language support (if model installed)
    print("\n\nExample 4: Multi-language Support")
    print("-" * 50)

    try:
        # Try loading Spanish model (requires: python -m spacy download es_core_news_sm)
        spacy_es = SpacyDetector(
            model="es_core_news_sm",
            language="es"
        )

        guard_es = PromptGuard(
            detectors=[spacy_es],
            policy="default_pii"
        )

        text_es = "Hola, soy María García de Barcelona. Mi correo es maria@ejemplo.es"

        anonymized_es, mapping_es = guard_es.anonymize(text_es)

        print(f"Original (Spanish):\n{text_es}")
        print(f"\nAnonymized:\n{anonymized_es}")
        print(f"\nMapping:\n{mapping_es}")

    except OSError:
        print("Spanish model not installed. Install with:")
        print("  python -m spacy download es_core_news_sm")

    # Example 5: Performance comparison
    print("\n\nExample 5: Performance Comparison")
    print("-" * 50)

    import time

    test_text = "Contact John Smith at john@example.com or 555-123-4567." * 100

    # Regex detector
    guard_regex = PromptGuard(detectors=["regex"])
    start = time.time()
    guard_regex.anonymize(test_text)
    regex_time = time.time() - start

    # spaCy detector
    guard_spacy = PromptGuard(detectors=["spacy"])
    start = time.time()
    guard_spacy.anonymize(test_text)
    spacy_time = time.time() - start

    print(f"Regex detector: {regex_time*1000:.2f}ms")
    print(f"spaCy detector: {spacy_time*1000:.2f}ms")
    print(f"Ratio: {spacy_time/regex_time:.1f}x slower (but more accurate)")

    print("\n✅ spaCy detector examples completed!")


if __name__ == "__main__":
    main()

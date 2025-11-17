"""
Examples of using the Synthetic Data Generator.

This file demonstrates how to generate realistic fake PII data
for testing, development, and demonstrations.

Run this file to see examples:
    python synthetic_data_examples.py
"""

from prompt_guard.synthetic import SyntheticDataGenerator
from prompt_guard import PromptGuard


def example_basic_generation():
    """Example 1: Basic PII generation."""
    print("=" * 70)
    print("Example 1: Basic PII Generation")
    print("=" * 70)

    gen = SyntheticDataGenerator(seed=42)  # Use seed for reproducibility

    # Generate different types of PII
    print("\nNames:")
    for name in gen.generate_pii("NAME", count=5):
        print(f"  - {name}")

    print("\nEmails:")
    for email in gen.generate_pii("EMAIL", count=5):
        print(f"  - {email}")

    print("\nPhone Numbers:")
    for phone in gen.generate_pii("PHONE", count=5):
        print(f"  - {phone}")

    print("\nSSNs:")
    for ssn in gen.generate_pii("SSN", count=3):
        print(f"  - {ssn}")

    print("\nCredit Cards:")
    for cc in gen.generate_pii("CREDIT_CARD", count=3):
        print(f"  - {cc}")

    print("\nAddresses:")
    for addr in gen.generate_pii("ADDRESS", count=3):
        print(f"  - {addr}")


def example_template_based_generation():
    """Example 2: Template-based text generation."""
    print("\n" + "=" * 70)
    print("Example 2: Template-Based Text Generation")
    print("=" * 70)

    gen = SyntheticDataGenerator(seed=42)

    template = "Contact {NAME} at {EMAIL} or call {PHONE} for more information."

    print(f"\nTemplate: {template}\n")
    print("Generated texts:")

    for text in gen.generate_text_with_pii(template, count=5):
        print(f"  {text}")


def example_dataset_generation():
    """Example 3: Dataset generation with multiple templates."""
    print("\n" + "=" * 70)
    print("Example 3: Dataset Generation")
    print("=" * 70)

    gen = SyntheticDataGenerator(seed=42)

    templates = [
        "User {NAME} ({USERNAME}) registered from {IP_ADDRESS}",
        "Payment processed for {NAME} using card {CREDIT_CARD}",
        "Shipping to {NAME} at {ADDRESS}",
        "Email {EMAIL} verified for account {USERNAME}",
    ]

    dataset = gen.generate_dataset(templates, samples_per_template=3)

    print(f"\nGenerated {len(dataset)} samples:\n")

    for item in dataset[:10]:  # Show first 10
        print(f"  [{item['id']}] {item['text']}")


def example_testing_anonymization():
    """Example 4: Using synthetic data to test anonymization."""
    print("\n" + "=" * 70)
    print("Example 4: Testing Anonymization with Synthetic Data")
    print("=" * 70)

    gen = SyntheticDataGenerator(seed=42)
    guard = PromptGuard(policy="default_pii")

    # Generate test texts
    template = "{NAME} can be reached at {EMAIL} or {PHONE}. SSN: {SSN}."

    test_texts = gen.generate_text_with_pii(template, count=3)

    print("\nTesting anonymization:")

    for i, text in enumerate(test_texts, 1):
        anonymized, mapping = guard.anonymize(text)

        print(f"\n  Test {i}:")
        print(f"    Original:    {text}")
        print(f"    Anonymized:  {anonymized}")
        print(f"    PII detected: {len(mapping)} entities")


def example_different_pii_types():
    """Example 5: Generate all supported PII types."""
    print("\n" + "=" * 70)
    print("Example 5: All Supported PII Types")
    print("=" * 70)

    gen = SyntheticDataGenerator(seed=42)

    pii_types = [
        "NAME",
        "EMAIL",
        "PHONE",
        "SSN",
        "CREDIT_CARD",
        "IP_ADDRESS",
        "IPV6",
        "ADDRESS",
        "CITY",
        "STATE",
        "ZIP_CODE",
        "DATE_OF_BIRTH",
        "URL",
        "USERNAME",
        "PASSWORD",
    ]

    print("\nGenerated PII examples:")

    for pii_type in pii_types:
        try:
            example = gen.generate_pii(pii_type, count=1)[0]
            print(f"  {pii_type:20s} → {example}")
        except ValueError as e:
            print(f"  {pii_type:20s} → Error: {e}")


def example_bulk_generation():
    """Example 6: Bulk data generation for load testing."""
    print("\n" + "=" * 70)
    print("Example 6: Bulk Data Generation")
    print("=" * 70)

    gen = SyntheticDataGenerator()

    # Generate large quantities for performance testing
    print("\nGenerating bulk data...")

    quantities = [100, 1000, 10000]

    for qty in quantities:
        emails = gen.generate_pii("EMAIL", count=qty)
        print(f"  Generated {len(emails):,} emails")


def example_custom_parameters():
    """Example 7: Using custom parameters."""
    print("\n" + "=" * 70)
    print("Example 7: Custom Parameters")
    print("=" * 70)

    gen = SyntheticDataGenerator()

    # Different phone formats
    print("\nUS Phone Numbers:")
    for phone in gen.generate_pii("PHONE", count=3, format_type="us"):
        print(f"  {phone}")

    print("\nInternational Phone Numbers:")
    for phone in gen.generate_pii("PHONE", count=3, format_type="intl"):
        print(f"  {phone}")

    # Different card types
    print("\nVisa Cards:")
    for card in gen.generate_pii("CREDIT_CARD", count=2, card_type="visa"):
        print(f"  {card}")

    print("\nAmerican Express Cards:")
    for card in gen.generate_pii("CREDIT_CARD", count=2, card_type="amex"):
        print(f"  {card}")

    # Date of birth with age range
    print("\nDates of Birth (18-30 years old):")
    for dob in gen.generate_pii("DATE_OF_BIRTH", count=3, min_age=18, max_age=30):
        print(f"  {dob}")


def example_reproducible_generation():
    """Example 8: Reproducible generation with seeds."""
    print("\n" + "=" * 70)
    print("Example 8: Reproducible Generation")
    print("=" * 70)

    print("\nGeneration 1 (seed=42):")
    gen1 = SyntheticDataGenerator(seed=42)
    emails1 = gen1.generate_pii("EMAIL", count=3)
    for email in emails1:
        print(f"  {email}")

    print("\nGeneration 2 (seed=42) - should be identical:")
    gen2 = SyntheticDataGenerator(seed=42)
    emails2 = gen2.generate_pii("EMAIL", count=3)
    for email in emails2:
        print(f"  {email}")

    print(f"\nAre they identical? {emails1 == emails2}")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Synthetic Data Generator Examples" + " " * 19 + "║")
    print("╚" + "=" * 68 + "╝")

    example_basic_generation()
    example_template_based_generation()
    example_dataset_generation()
    example_testing_anonymization()
    example_different_pii_types()
    example_bulk_generation()
    example_custom_parameters()
    example_reproducible_generation()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

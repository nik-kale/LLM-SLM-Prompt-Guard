"""
Example: Multi-language PII detection and protection.

This example demonstrates how to use llm-slm-prompt-guard with multiple
languages using spaCy and Presidio ML-based detectors.

Installation:
    pip install llm-slm-prompt-guard[spacy,presidio]

    # Download language models
    python -m spacy download en_core_web_sm  # English
    python -m spacy download es_core_news_sm  # Spanish
    python -m spacy download fr_core_news_sm  # French
    python -m spacy download de_core_news_sm  # German
    python -m spacy download it_core_news_sm  # Italian

Usage:
    python examples/multilanguage_example.py
"""

from prompt_guard import PromptGuard


def example_1_english():
    """Example 1: English (baseline)."""
    print("\n" + "=" * 60)
    print("Example 1: English")
    print("=" * 60)

    guard = PromptGuard(
        detectors=["enhanced_regex", "spacy"],
        policy="default_pii"
    )

    text = """
    Hello, I'm Dr. Sarah Johnson from Boston Medical Center.
    You can reach me at sarah.johnson@hospital.com or call 617-555-1234.
    My patient John Smith (SSN: 123-45-6789) needs a follow-up.
    """

    anonymized, mapping = guard.anonymize(text)

    print(f"Original:\n{text}")
    print(f"\nAnonymized:\n{anonymized}")
    print(f"\nDetected entities: {list(mapping.keys())}")


def example_2_spanish():
    """Example 2: Spanish."""
    print("\n" + "=" * 60)
    print("Example 2: Spanish (Español)")
    print("=" * 60)

    try:
        from prompt_guard.detectors.spacy_detector import SpacyDetector

        # Create Spanish detector
        spacy_es = SpacyDetector(
            model="es_core_news_sm",
            language="es",
            confidence_threshold=0.6,
        )

        guard = PromptGuard(
            detectors=["enhanced_regex", spacy_es],
            policy="default_pii"
        )

        text = """
        Hola, soy la Dra. María García del Hospital Central de Barcelona.
        Puedes contactarme en maria.garcia@hospital.es o llamar al +34 93 555 1234.
        Mi paciente Juan Pérez necesita una consulta de seguimiento.
        Correo alternativo: juan.perez@email.es
        """

        anonymized, mapping = guard.anonymize(text)

        print(f"Original:\n{text}")
        print(f"\nAnonymized:\n{anonymized}")
        print(f"\nDetected entities: {list(mapping.keys())}")

    except OSError:
        print("❌ Spanish model not installed.")
        print("   Install with: python -m spacy download es_core_news_sm")


def example_3_french():
    """Example 3: French."""
    print("\n" + "=" * 60)
    print("Example 3: French (Français)")
    print("=" * 60)

    try:
        from prompt_guard.detectors.spacy_detector import SpacyDetector

        # Create French detector
        spacy_fr = SpacyDetector(
            model="fr_core_news_sm",
            language="fr",
            confidence_threshold=0.6,
        )

        guard = PromptGuard(
            detectors=["enhanced_regex", spacy_fr],
            policy="default_pii"
        )

        text = """
        Bonjour, je suis Dr. Pierre Dubois de l'Hôpital Paris.
        Vous pouvez me contacter à pierre.dubois@hopital.fr ou appeler le +33 1 55 12 34 56.
        Mon patient Jean Martin (email: jean.martin@email.fr) a besoin d'un rendez-vous.
        """

        anonymized, mapping = guard.anonymize(text)

        print(f"Original:\n{text}")
        print(f"\nAnonymized:\n{anonymized}")
        print(f"\nDetected entities: {list(mapping.keys())}")

    except OSError:
        print("❌ French model not installed.")
        print("   Install with: python -m spacy download fr_core_news_sm")


def example_4_german():
    """Example 4: German."""
    print("\n" + "=" * 60)
    print("Example 4: German (Deutsch)")
    print("=" * 60)

    try:
        from prompt_guard.detectors.spacy_detector import SpacyDetector

        # Create German detector
        spacy_de = SpacyDetector(
            model="de_core_news_sm",
            language="de",
            confidence_threshold=0.6,
        )

        guard = PromptGuard(
            detectors=["enhanced_regex", spacy_de],
            policy="default_pii"
        )

        text = """
        Guten Tag, ich bin Dr. Hans Müller vom Krankenhaus Berlin.
        Sie können mich unter hans.mueller@krankenhaus.de erreichen oder +49 30 555 1234 anrufen.
        Mein Patient Klaus Schmidt (E-Mail: klaus.schmidt@email.de) braucht einen Termin.
        """

        anonymized, mapping = guard.anonymize(text)

        print(f"Original:\n{text}")
        print(f"\nAnonymized:\n{anonymized}")
        print(f"\nDetected entities: {list(mapping.keys())}")

    except OSError:
        print("❌ German model not installed.")
        print("   Install with: python -m spacy download de_core_news_sm")


def example_5_italian():
    """Example 5: Italian."""
    print("\n" + "=" * 60)
    print("Example 5: Italian (Italiano)")
    print("=" * 60)

    try:
        from prompt_guard.detectors.spacy_detector import SpacyDetector

        # Create Italian detector
        spacy_it = SpacyDetector(
            model="it_core_news_sm",
            language="it",
            confidence_threshold=0.6,
        )

        guard = PromptGuard(
            detectors=["enhanced_regex", spacy_it],
            policy="default_pii"
        )

        text = """
        Salve, sono il Dr. Marco Rossi dell'Ospedale di Roma.
        Potete contattarmi a marco.rossi@ospedale.it o chiamare +39 06 555 1234.
        Il mio paziente Giuseppe Bianchi (email: giuseppe.bianchi@email.it) ha bisogno di una visita.
        """

        anonymized, mapping = guard.anonymize(text)

        print(f"Original:\n{text}")
        print(f"\nAnonymized:\n{anonymized}")
        print(f"\nDetected entities: {list(mapping.keys())}")

    except OSError:
        print("❌ Italian model not installed.")
        print("   Install with: python -m spacy download it_core_news_sm")


def example_6_presidio_multilanguage():
    """Example 6: Using Presidio for multi-language support."""
    print("\n" + "=" * 60)
    print("Example 6: Presidio Multi-language")
    print("=" * 60)

    try:
        from prompt_guard.detectors.presidio_detector import PresidioDetector

        # Presidio supports multiple languages
        languages = [
            ("en", "Hello, contact me at john@example.com or 555-123-4567"),
            ("es", "Hola, contáctame en juan@ejemplo.es o 555-123-4567"),
            ("fr", "Bonjour, contactez-moi à jean@exemple.fr ou 555-123-4567"),
            ("de", "Hallo, kontaktieren Sie mich unter hans@beispiel.de oder 555-123-4567"),
        ]

        for lang_code, text in languages:
            print(f"\n{lang_code.upper()}:")

            # Create detector for language
            presidio = PresidioDetector(
                language=lang_code,
                score_threshold=0.5,
            )

            guard = PromptGuard(
                detectors=[presidio],
                policy="default_pii"
            )

            anonymized, mapping = guard.anonymize(text)

            print(f"  Original: {text}")
            print(f"  Anonymized: {anonymized}")
            print(f"  Entities: {list(mapping.keys())}")

    except ImportError:
        print("❌ Presidio not installed.")
        print("   Install with: pip install llm-slm-prompt-guard[presidio]")


def example_7_mixed_language():
    """Example 7: Handling mixed-language text."""
    print("\n" + "=" * 60)
    print("Example 7: Mixed Language Text")
    print("=" * 60)

    # Use regex + multiple language detectors
    guard = PromptGuard(
        detectors=["enhanced_regex"],  # Works across languages
        policy="default_pii"
    )

    text = """
    Multi-language contact info:
    - English: contact@company.com, +1-555-123-4567
    - Spanish: contacto@empresa.es, +34-91-555-1234
    - French: contact@entreprise.fr, +33-1-55-12-34-56
    - German: kontakt@firma.de, +49-30-555-1234
    - Italian: contatto@azienda.it, +39-06-555-1234
    """

    anonymized, mapping = guard.anonymize(text)

    print(f"Original:\n{text}")
    print(f"\nAnonymized:\n{anonymized}")
    print(f"\nDetected {len(mapping)} entities across multiple languages")


def example_8_language_specific_policies():
    """Example 8: Language-specific custom policies."""
    print("\n" + "=" * 60)
    print("Example 8: Language-Specific Policies")
    print("=" * 60)

    # Different regions have different PII requirements
    # For example, EU GDPR vs US HIPAA

    print("\nEU (GDPR) - Strict policy:")
    guard_eu = PromptGuard(policy="gdpr_strict")

    text_eu = """
    EU Citizen: Name: John Doe
    Email: john@example.eu
    IBAN: DE89 3704 0044 0532 0130 00
    IP: 2001:0db8:85a3:0000:0000:8a2e:0370:7334
    """

    anonymized_eu, mapping_eu = guard_eu.anonymize(text_eu)
    print(f"Original: {text_eu}")
    print(f"Anonymized: {anonymized_eu}")

    print("\nUS (HIPAA) - Healthcare policy:")
    guard_us = PromptGuard(policy="hipaa_phi")

    text_us = """
    Patient: Jane Smith
    SSN: 123-45-6789
    MRN: MRN-987654
    Phone: 555-123-4567
    """

    anonymized_us, mapping_us = guard_us.anonymize(text_us)
    print(f"Original: {text_us}")
    print(f"Anonymized: {anonymized_us}")

    print("\n✓ Different policies for different regions/regulations")


def example_9_translation_safe():
    """Example 9: Translation-safe anonymization."""
    print("\n" + "=" * 60)
    print("Example 9: Translation-Safe Anonymization")
    print("=" * 60)

    # When translating text, preserve PII placeholders
    guard = PromptGuard(policy="default_pii")

    # Original English text
    text_en = "Contact Dr. Sarah Johnson at sarah@hospital.com or 555-1234"

    anonymized_en, mapping = guard.anonymize(text_en)
    print(f"Original (EN): {text_en}")
    print(f"Anonymized (EN): {anonymized_en}")

    # Simulate translation (in real app, use a translation API)
    # The placeholders should be preserved during translation
    translated_es = anonymized_en.replace("Contact", "Contactar")
    translated_es = translated_es.replace("at", "en")
    translated_es = translated_es.replace("or", "o")

    print(f"\nTranslated (ES): {translated_es}")

    # De-anonymize in any language
    deanonymized_es = guard.deanonymize(translated_es, mapping)
    print(f"De-anonymized (ES): {deanonymized_es}")

    print("\n✓ Placeholders preserved across translation")


def main():
    print("=" * 60)
    print("Multi-language PII Detection Examples")
    print("=" * 60)

    print("\nSupported Languages:")
    print("  ✓ English (en)")
    print("  ✓ Spanish (es)")
    print("  ✓ French (fr)")
    print("  ✓ German (de)")
    print("  ✓ Italian (it)")
    print("  ✓ And more with Presidio...")

    # Run examples
    try:
        example_1_english()
        example_2_spanish()
        example_3_french()
        example_4_german()
        example_5_italian()
        example_6_presidio_multilanguage()
        example_7_mixed_language()
        example_8_language_specific_policies()
        example_9_translation_safe()

        print("\n" + "=" * 60)
        print("✅ All multi-language examples completed!")
        print("=" * 60)

        print("\nKey Features:")
        print("  ✓ spaCy support for 10+ languages")
        print("  ✓ Presidio support for 50+ languages")
        print("  ✓ Enhanced regex works across languages")
        print("  ✓ Language-specific policies (GDPR, HIPAA)")
        print("  ✓ Translation-safe placeholders")
        print("  ✓ Mixed-language text handling")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

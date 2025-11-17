"""
Unit tests for PromptGuard core functionality.
"""

import pytest
from prompt_guard import PromptGuard
from prompt_guard.types import AnonymizeOptions


class TestPromptGuardBasic:
    """Test basic anonymization and de-anonymization."""

    def test_init_default(self):
        """Test initialization with default settings."""
        guard = PromptGuard()
        assert guard is not None
        assert len(guard.detectors) > 0
        assert guard.policy is not None

    def test_init_custom_policy(self):
        """Test initialization with custom policy."""
        guard = PromptGuard(policy="gdpr_strict")
        assert guard.policy["name"] == "gdpr_strict"

    def test_anonymize_email(self):
        """Test email anonymization."""
        guard = PromptGuard(policy="default_pii")
        text = "Contact me at john@example.com"

        anonymized, mapping = guard.anonymize(text)

        assert "[EMAIL_1]" in anonymized
        assert "john@example.com" not in anonymized
        assert mapping["[EMAIL_1]"] == "john@example.com"

    def test_anonymize_phone(self):
        """Test phone number anonymization."""
        guard = PromptGuard(policy="default_pii")
        text = "Call me at 555-123-4567"

        anonymized, mapping = guard.anonymize(text)

        assert "[PHONE_1]" in anonymized
        assert "555-123-4567" not in anonymized

    def test_anonymize_person_name(self):
        """Test person name anonymization."""
        guard = PromptGuard(policy="default_pii")
        text = "My name is John Smith"

        anonymized, mapping = guard.anonymize(text)

        assert "[NAME_1]" in anonymized or "[USER_1]" in anonymized
        assert "John Smith" not in anonymized

    def test_anonymize_multiple_pii(self):
        """Test multiple PII types in one text."""
        guard = PromptGuard(policy="default_pii")
        text = "John Smith's email is john@example.com and phone is 555-123-4567"

        anonymized, mapping = guard.anonymize(text)

        # Should detect name, email, and phone
        assert len(mapping) >= 2  # At least email and phone

    def test_deanonymize(self):
        """Test de-anonymization."""
        guard = PromptGuard(policy="default_pii")
        original = "Email: john@example.com"

        anonymized, mapping = guard.anonymize(original)
        restored = guard.deanonymize(anonymized, mapping)

        assert original == restored

    def test_deanonymize_partial(self):
        """Test de-anonymization with partial mapping."""
        guard = PromptGuard()
        mapping = {
            "[EMAIL_1]": "john@example.com",
            "[NAME_1]": "John Smith",
        }

        text = "Contact [NAME_1] at [EMAIL_1] for more info"
        deanonymized = guard.deanonymize(text, mapping)

        assert deanonymized == "Contact John Smith at john@example.com for more info"

    def test_batch_anonymize(self):
        """Test batch anonymization."""
        guard = PromptGuard()
        texts = [
            "Email: john@example.com",
            "Phone: 555-123-4567",
            "Name: Jane Doe",
        ]

        results = guard.batch_anonymize(texts)

        assert len(results) == 3
        for anonymized, mapping in results:
            assert isinstance(anonymized, str)
            assert isinstance(mapping, dict)

    def test_empty_text(self):
        """Test with empty text."""
        guard = PromptGuard()
        anonymized, mapping = guard.anonymize("")

        assert anonymized == ""
        assert len(mapping) == 0

    def test_no_pii(self):
        """Test text with no PII."""
        guard = PromptGuard()
        text = "This is a simple message without any sensitive information."

        anonymized, mapping = guard.anonymize(text)

        assert anonymized == text
        assert len(mapping) == 0


class TestPromptGuardDetectors:
    """Test different detector configurations."""

    def test_regex_detector(self):
        """Test regex detector specifically."""
        guard = PromptGuard(detectors=["regex"])
        text = "Email: test@example.com"

        anonymized, mapping = guard.anonymize(text)

        assert len(mapping) > 0

    @pytest.mark.skipif(
        not pytest.importorskip("presidio_analyzer", minversion=None),
        reason="Presidio not installed",
    )
    def test_presidio_detector(self):
        """Test Presidio detector if available."""
        guard = PromptGuard(detectors=["presidio"])
        text = "My name is John and email is john@example.com"

        anonymized, mapping = guard.anonymize(text)

        # Presidio should detect more entities
        assert len(mapping) >= 1


class TestPromptGuardPolicies:
    """Test different policy configurations."""

    def test_default_pii_policy(self):
        """Test default_pii policy."""
        guard = PromptGuard(policy="default_pii")
        assert guard.policy["name"] == "default_pii"

    def test_gdpr_strict_policy(self):
        """Test gdpr_strict policy."""
        guard = PromptGuard(policy="gdpr_strict")
        assert guard.policy["name"] == "gdpr_strict"

    def test_slm_local_policy(self):
        """Test slm_local policy (shorter placeholders)."""
        guard = PromptGuard(policy="slm_local")
        text = "Email: test@example.com"

        anonymized, mapping = guard.anonymize(text)

        # SLM policy should use shorter placeholders
        assert "[EMAIL_" in anonymized


class TestPromptGuardEdgeCases:
    """Test edge cases and error handling."""

    def test_special_characters(self):
        """Test text with special characters."""
        guard = PromptGuard()
        text = "Email: test+tag@example.com with special chars!"

        anonymized, mapping = guard.anonymize(text)

        assert "[EMAIL_1]" in anonymized

    def test_unicode_text(self):
        """Test with Unicode text."""
        guard = PromptGuard()
        text = "Email: test@example.com in 中文"

        anonymized, mapping = guard.anonymize(text)

        assert "[EMAIL_1]" in anonymized
        assert "中文" in anonymized  # Unicode should be preserved

    def test_very_long_text(self):
        """Test with very long text."""
        guard = PromptGuard()
        text = "Email: test@example.com. " + "x" * 10000

        anonymized, mapping = guard.anonymize(text)

        assert "[EMAIL_1]" in anonymized
        assert len(anonymized) > 10000

    def test_repeated_pii(self):
        """Test same PII appearing multiple times."""
        guard = PromptGuard()
        text = "Email test@example.com twice: test@example.com"

        anonymized, mapping = guard.anonymize(text)

        # Should map to same placeholder
        assert anonymized.count("[EMAIL_1]") == 2

    def test_overlapping_patterns(self):
        """Test overlapping PII patterns."""
        guard = PromptGuard()
        text = "john.smith@example.com"  # Could be name + email

        anonymized, mapping = guard.anonymize(text)

        # Should detect as email, not as separate name components
        assert "[EMAIL_1]" in anonymized


class TestPromptGuardPerformance:
    """Performance-related tests."""

    def test_performance_small_text(self, benchmark):
        """Benchmark small text anonymization."""
        guard = PromptGuard()
        text = "Email: test@example.com"

        result = benchmark(guard.anonymize, text)
        assert result[0] is not None

    def test_performance_batch(self, benchmark):
        """Benchmark batch processing."""
        guard = PromptGuard()
        texts = ["Email: test@example.com"] * 100

        result = benchmark(guard.batch_anonymize, texts)
        assert len(result) == 100

"""
Tests for overlap resolution between detections.

Every test here asserts on the anonymized text: an overlap bug in a PII
guard shows up as original characters surviving in the output.
"""

import time

import pytest

from prompt_guard import OverlapStrategy, PromptGuard
from prompt_guard.detectors import BaseDetector
from prompt_guard.types import DetectorResult


class StubDetector(BaseDetector):
    """Detector that returns fixed spans, for constructing overlap cases."""

    def __init__(self, *spans):
        self.spans = spans

    def detect(self, text):
        return [
            DetectorResult(entity_type=t, start=s, end=e, text=text[s:e], confidence=c)
            for t, s, e, c in self.spans
        ]


def guard_with(*spans, strategy=OverlapStrategy.LONGEST_MATCH, **kwargs):
    guard = PromptGuard(overlap_strategy=strategy, **kwargs)
    guard.detectors = [StubDetector(*spans)]
    return guard


ALL_STRATEGIES = list(OverlapStrategy)


class TestNoPartialLeaks:
    @pytest.mark.parametrize("strategy", ALL_STRATEGIES)
    def test_chained_overlaps_are_fully_redacted(self, strategy):
        # A and C overlap by one character and C is longer; B sits inside A.
        # Keeping only C used to leave text[0:9] (most of A) in the output.
        text = "0123456789ABCDEFGHIJ tail"
        guard = guard_with(
            ("EMAIL", 0, 10, 0.9),
            ("PHONE", 5, 8, 0.8),
            ("PERSON", 9, 20, 0.7),
            strategy=strategy,
        )

        anonymized, mapping = guard.anonymize(text)

        assert anonymized.endswith("] tail")
        assert "0123" not in anonymized and "ABCD" not in anonymized
        assert list(mapping.values()) == ["0123456789ABCDEFGHIJ"]

    @pytest.mark.parametrize("strategy", ALL_STRATEGIES)
    def test_contained_entity_of_another_type_does_not_leak(self, strategy):
        # PHONE_RE matches the digits inside the email's local part. Under the
        # merge strategy both used to be kept and the replacement loop then
        # re-emitted the tail of the email after the placeholders.
        guard = PromptGuard(overlap_strategy=strategy)

        anonymized, mapping = guard.anonymize("Mail x12345678901@ex.com please")

        assert anonymized == "Mail [EMAIL_1] please"
        assert mapping == {"[EMAIL_1]": "x12345678901@ex.com"}

    def test_merged_entities_keep_their_original_text(self):
        guard = guard_with(
            ("EMAIL", 0, 5, 0.8),
            ("EMAIL", 3, 9, 0.6),
            strategy=OverlapStrategy.MERGE_SAME_TYPE,
        )

        anonymized, mapping = guard.anonymize("abcdefghi rest")

        assert anonymized == "[EMAIL_1] rest"
        assert mapping == {"[EMAIL_1]": "abcdefghi"}
        assert guard.deanonymize(anonymized, mapping) == "abcdefghi rest"


class TestPolicyAwareResolution:
    def test_unconfigured_type_cannot_hide_configured_entity(self, tmp_path):
        # PHONE_RE also matches SSNs and card numbers. With a policy that only
        # redacts SSN and CREDIT_CARD, the PHONE detection used to win the tie
        # and was then dropped as unconfigured, so the SSN went out in clear.
        policy = tmp_path / "ids_only.yaml"
        policy.write_text(
            "name: ids_only\n"
            "entities:\n"
            "  SSN:\n"
            '    placeholder: "[SSN_{i}]"\n'
            "  CREDIT_CARD:\n"
            '    placeholder: "[CC_{i}]"\n'
        )
        guard = PromptGuard(custom_policy_path=str(policy))

        anonymized, _ = guard.anonymize("SSN 123-45-6789, card 4111 1111 1111 1111")

        assert anonymized == "SSN [SSN_1], card [CC_1]"

    def test_identical_spans_prefer_the_more_sensitive_type(self):
        guard = PromptGuard(policy="default_pii")

        assert guard.anonymize("SSN: 123-45-6789")[0] == "SSN: [SSN_1]"
        assert guard.anonymize("Card 4111-1111-1111-1111")[0] == "Card [CC_1]"

    def test_first_detector_strategy_uses_detector_order(self):
        guard = guard_with(
            ("PERSON", 4, 14, 0.5),
            ("EMAIL", 0, 20, 0.9),
            strategy=OverlapStrategy.FIRST_DETECTOR,
        )

        anonymized, mapping = guard.anonymize("abcdefghijklmnopqrst")

        assert anonymized == "[NAME_1]"
        assert mapping == {"[NAME_1]": "abcdefghijklmnopqrst"}


def test_resolution_scales_to_many_entities():
    guard = PromptGuard()
    text = "x@y.com 555-123-4567 " * 20_000

    start = time.perf_counter()
    anonymized, _ = guard.anonymize(text)
    duration = time.perf_counter() - start

    assert "@" not in anonymized
    assert duration < 5.0

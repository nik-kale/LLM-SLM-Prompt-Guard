"""
Unit tests for the regex-based detectors.
"""

import pytest

from prompt_guard.detectors import EnhancedRegexDetector, RegexDetector


def _overlapping_pairs(results):
    spans = sorted((r.start, r.end) for r in results)
    return [
        (a, b)
        for i, a in enumerate(spans)
        for b in spans[i + 1 :]
        if not (a[1] <= b[0] or b[1] <= a[0])
    ]


class TestEnhancedRegexDetector:
    @pytest.mark.parametrize(
        "text",
        [
            # A lower-priority PHONE match that fully contains a higher-priority SSN
            "Reference (480603731 8 on file",
            "Call +1 555 123 4567 or SSN 123-45-6789",
            "Dr. John Smith, MRN 1234567, DOB 03/15/1985",
        ],
    )
    def test_results_never_overlap(self, text):
        results = EnhancedRegexDetector().detect(text)
        assert results
        assert _overlapping_pairs(results) == []

    def test_higher_priority_match_wins_containment(self):
        results = EnhancedRegexDetector().detect("Reference (480603731 8 on file")
        assert [(r.entity_type, r.text) for r in results] == [("SSN", "480603731")]


class TestEmailPatterns:
    @pytest.mark.parametrize("detector_cls", [RegexDetector, EnhancedRegexDetector])
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Contact john.smith@example.com today", "john.smith@example.com"),
            ("tag: test+tag@example.co.uk.", "test+tag@example.co.uk"),
            ("<a_b-c@mail.example.org>", "a_b-c@mail.example.org"),
        ],
    )
    def test_email_spans_unchanged(self, detector_cls, text, expected):
        emails = [r.text for r in detector_cls().detect(text) if r.entity_type == "EMAIL"]
        assert emails == [expected]

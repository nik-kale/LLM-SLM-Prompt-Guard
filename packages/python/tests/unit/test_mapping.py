"""
Tests for placeholder assignment and de-anonymization.

A placeholder that maps to two different values silently restores the
wrong person's data, so these tests check round trips, not just output
shape.
"""

from prompt_guard import PromptGuard
from prompt_guard.detectors import BaseDetector
from prompt_guard.types import DetectorResult


class StubDetector(BaseDetector):
    """Detector that labels fixed substrings."""

    def __init__(self, **labels):
        self.labels = labels  # substring -> entity type

    def detect(self, text):
        results = []
        for value, entity_type in self.labels.items():
            start = text.find(value)
            while start != -1:
                results.append(
                    DetectorResult(entity_type, start, start + len(value), value)
                )
                start = text.find(value, start + 1)
        return results


class TestPlaceholderAssignment:
    def test_repeated_value_reuses_placeholder(self):
        guard = PromptGuard()
        text = "Write to a@example.com, b@example.com, then a@example.com again"

        anonymized, mapping = guard.anonymize(text)

        assert anonymized == "Write to [EMAIL_1], [EMAIL_2], then [EMAIL_1] again"
        assert mapping == {"[EMAIL_1]": "a@example.com", "[EMAIL_2]": "b@example.com"}

    def test_types_sharing_a_template_get_distinct_placeholders(self):
        # hipaa_phi uses "[DATE_{i}]" for both DOB and DATE_TIME. Separate
        # counters per type used to give both values "[DATE_1]".
        guard = PromptGuard(policy="hipaa_phi")
        guard.detectors = [StubDetector(**{"1985-03-15": "DOB", "next Tuesday": "DATE_TIME"})]
        text = "Born 1985-03-15, seen next Tuesday"

        anonymized, mapping = guard.anonymize(text)

        assert anonymized == "Born [DATE_1], seen [DATE_2]"
        assert guard.deanonymize(anonymized, mapping) == text

    def test_values_marked_not_storable_stay_out_of_the_mapping(self):
        # pci_dss marks CVV with storage_allowed: false.
        guard = PromptGuard(policy="pci_dss")
        guard.detectors = [StubDetector(**{"4111111111111111": "CREDIT_CARD", "737": "CVV"})]

        anonymized, mapping = guard.anonymize("Card 4111111111111111 CVV 737")

        assert anonymized == "Card [PAN_1] CVV [REDACTED]"
        assert mapping == {"[PAN_1]": "4111111111111111"}
        assert "737" not in mapping.values()


class TestExistingMapping:
    def test_messages_sharing_a_mapping_do_not_collide(self):
        guard = PromptGuard()

        first, mapping = guard.anonymize("I am alice@example.com")
        second, mapping2 = guard.anonymize(
            "Forward to bob@example.com and alice@example.com",
            existing_mapping=mapping,
        )

        assert first == "I am [EMAIL_1]"
        assert second == "Forward to [EMAIL_2] and [EMAIL_1]"
        assert mapping == {"[EMAIL_1]": "alice@example.com"}  # not mutated
        assert mapping2 == {
            "[EMAIL_1]": "alice@example.com",
            "[EMAIL_2]": "bob@example.com",
        }
        reply = "Sent [EMAIL_2] a copy for [EMAIL_1]"
        assert (
            guard.deanonymize(reply, mapping2)
            == "Sent bob@example.com a copy for alice@example.com"
        )

    def test_numbering_skips_placeholders_already_in_use(self):
        guard = PromptGuard()

        anonymized, mapping = guard.anonymize(
            "Mail c@example.com",
            existing_mapping={"[EMAIL_1]": "a@example.com", "[EMAIL_2]": "b@example.com"},
        )

        assert anonymized == "Mail [EMAIL_3]"
        assert mapping["[EMAIL_3]"] == "c@example.com"


class TestDeanonymize:
    def test_round_trip(self):
        guard = PromptGuard()
        text = (
            "John Smith (john@example.com, 555-123-4567) paid with "
            "4111 1111 1111 1111; John Smith confirmed from 10.0.0.1."
        )

        anonymized, mapping = guard.anonymize(text)

        assert guard.deanonymize(anonymized, mapping) == text

    def test_placeholder_prefixes_do_not_collide(self):
        # With a template like "NAME_{i}", replacing "NAME_1" first used to
        # turn "NAME_10" into "Ann0".
        guard = PromptGuard()
        mapping = {"NAME_1": "Ann", "NAME_10": "Bob"}

        assert guard.deanonymize("NAME_10 met NAME_1", mapping) == "Bob met Ann"

    def test_restored_values_are_not_rescanned(self):
        guard = PromptGuard()
        mapping = {"[NAME_1]": "literal [EMAIL_1] text", "[EMAIL_1]": "x@example.com"}

        assert (
            guard.deanonymize("[NAME_1] / [EMAIL_1]", mapping)
            == "literal [EMAIL_1] text / x@example.com"
        )

"""
Tests for the hash, mask and synthetic anonymization strategies.
"""

import hashlib
import hmac

import pytest

from prompt_guard.anonymizers import HashAnonymizer, MaskAnonymizer


class TestHashAnonymizer:
    def test_hash_is_keyed_not_a_plain_digest(self):
        # An unsalted SHA-256 of an SSN can be reversed by hashing all 10^9
        # possible SSNs; the default must not produce one.
        hashed = HashAnonymizer().anonymize_entity("SSN", "123-45-6789", 1)

        assert hashed != hashlib.sha256(b"123-45-6789").hexdigest()

    def test_without_salt_each_instance_uses_its_own_key(self):
        first = HashAnonymizer()
        second = HashAnonymizer()

        a = first.anonymize_entity("EMAIL", "a@example.com", 1)

        assert first.anonymize_entity("EMAIL", "a@example.com", 2) == a
        assert second.anonymize_entity("EMAIL", "a@example.com", 1) != a

    def test_salt_gives_stable_hmac(self):
        hashed = HashAnonymizer(salt="s3cret").anonymize_entity("EMAIL", "a@example.com", 1)

        assert hashed == HashAnonymizer(salt="s3cret").anonymize_entity("EMAIL", "a@example.com", 1)
        assert hashed == hmac.new(b"s3cret", b"a@example.com", "sha256").hexdigest()
        assert hashed != hashlib.sha256(b"s3creta@example.com").hexdigest()

    def test_sha512_and_truncate(self):
        hashed = HashAnonymizer(algorithm="sha512", salt="k", truncate=12).anonymize_entity(
            "EMAIL", "a@example.com", 1
        )

        assert hashed == hmac.new(b"k", b"a@example.com", "sha512").hexdigest()[:12]

    def test_md5_is_rejected(self):
        with pytest.raises(ValueError):
            HashAnonymizer(algorithm="md5")


class TestMaskAnonymizer:
    def test_reveal_last_digits(self):
        masked = MaskAnonymizer(reveal_last=4).anonymize_entity("PHONE", "555-123-4567", 1)

        assert masked == "***-***-4567"


class TestSyntheticAnonymizer:
    @pytest.fixture(autouse=True)
    def _require_faker(self):
        pytest.importorskip("faker")

    def _cls(self):
        from prompt_guard.anonymizers.synthetic import SyntheticAnonymizer

        return SyntheticAnonymizer

    def test_same_input_same_output_within_instance(self):
        anonymizer = self._cls()()

        first = anonymizer.anonymize_entity("PERSON", "John Smith", 1)

        assert anonymizer.anonymize_entity("PERSON", "John Smith", 2) == first
        assert first != "John Smith"

    def test_unseeded_instances_are_not_linkable(self):
        # The fake used to be seeded from md5(original), so anyone could map a
        # synthetic value back to its original by trying candidate values.
        cls = self._cls()
        originals = [f"{n:03d}-45-6789" for n in range(20)]

        first = [cls().anonymize_entity("SSN", value, 1) for value in originals]
        second = [cls().anonymize_entity("SSN", value, 1) for value in originals]

        assert first != second

    def test_seed_makes_output_reproducible(self):
        cls = self._cls()

        assert cls(seed=7).anonymize_entity("EMAIL", "a@example.com", 1) == cls(
            seed=7
        ).anonymize_entity("EMAIL", "a@example.com", 1)

    def test_distinct_originals_never_share_a_synthetic_value(self):
        # Unknown types fall back to fake.word(), whose vocabulary is small
        # enough that collisions used to overwrite mapping entries.
        anonymizer = self._cls()()
        originals = [f"secret-{i}" for i in range(2000)]

        synthetic = [anonymizer.anonymize_entity("CUSTOM", value, i) for i, value in enumerate(originals)]

        assert len(set(synthetic)) == len(originals)
        assert anonymizer.get_mapping() == dict(zip(synthetic, originals))

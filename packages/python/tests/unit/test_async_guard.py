"""
Tests for AsyncPromptGuard and callers that anonymize several texts
into one mapping.
"""

import asyncio

import pytest

from prompt_guard import AsyncPromptGuard, OverlapStrategy, PromptGuard
from prompt_guard.adapters import VercelAIAdapter


async def _chunks(*parts):
    for part in parts:
        yield part


async def _collect(agen):
    return [item async for item in agen]


class TestAsyncMatchesSync:
    @pytest.mark.parametrize(
        "text",
        [
            "SSN 123-45-6789",
            "Mail x12345678901@ex.com please",
            "John Smith, john@example.com, john@example.com",
        ],
    )
    @pytest.mark.parametrize("strategy", list(OverlapStrategy))
    def test_same_result_as_prompt_guard(self, text, strategy):
        # AsyncPromptGuard used to skip overlap resolution, which emitted
        # placeholders twice and leaked the tail of the email ("@ex.com").
        expected = PromptGuard(overlap_strategy=strategy).anonymize(text)
        guard = AsyncPromptGuard(overlap_strategy=strategy)

        assert asyncio.run(guard.anonymize_async(text)) == expected

    def test_batch_larger_than_concurrency_limit(self):
        guard = AsyncPromptGuard(max_concurrent=2)
        texts = [f"Email: user{i}@example.com" for i in range(10)]

        results = asyncio.run(guard.batch_anonymize(texts))

        assert [r[0] for r in results] == ["Email: [EMAIL_1]"] * 10
        assert [r[1]["[EMAIL_1]"] for r in results] == [f"user{i}@example.com" for i in range(10)]


class TestStreamAnonymize:
    def test_entities_split_across_chunks_are_detected(self):
        guard = AsyncPromptGuard()
        text = (
            "Hello team, please reach alice.jones@example.com about the invoice. "
            "Bob can be reached on 555-123-4567 tomorrow, and alice.jones@example.com "
            "will forward it to carol@example.org before noon. " * 3
        )
        # 7-character chunks split every email and phone number
        parts = [text[i : i + 7] for i in range(0, len(text), 7)]

        pieces = asyncio.run(_collect(guard.stream_anonymize(_chunks(*parts), chunk_size=40)))

        anonymized = "".join(piece for piece, _ in pieces)
        mapping = pieces[-1][1]
        assert len(pieces) > 1
        assert "@" not in anonymized and "555-123" not in anonymized
        assert guard._guard.deanonymize(anonymized, mapping) == text

    def test_placeholders_are_unique_across_pieces(self):
        guard = AsyncPromptGuard()
        text = " ".join(f"user{i}@example.com" for i in range(30))

        pieces = asyncio.run(_collect(guard.stream_anonymize(_chunks(text), chunk_size=50)))

        mapping = pieces[-1][1]
        assert len(pieces) > 1
        assert sorted(mapping.values()) == sorted(f"user{i}@example.com" for i in range(30))


class TestVercelAdapter:
    @pytest.mark.parametrize("guard_cls", [PromptGuard, AsyncPromptGuard])
    def test_messages_share_one_mapping(self, guard_cls):
        # With AsyncPromptGuard the adapter used to read result.anonymized
        # from a tuple and raise AttributeError.
        adapter = VercelAIAdapter(guard_cls())
        messages = [
            {"role": "user", "content": "I am alice@example.com"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "user", "content": "Loop in bob@example.com"},
        ]

        protected, mapping = asyncio.run(adapter.protect_messages(messages))

        assert [m["content"] for m in protected] == [
            "I am [EMAIL_1]",
            "Hi!",
            "Loop in [EMAIL_2]",
        ]
        assert mapping == {"[EMAIL_1]": "alice@example.com", "[EMAIL_2]": "bob@example.com"}

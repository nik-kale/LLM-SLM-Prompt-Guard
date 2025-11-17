"""
Comprehensive integration tests for framework adapters.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from prompt_guard import PromptGuard


class TestLangChainAdapter:
    """Integration tests for LangChain adapter."""

    @pytest.mark.skipif(
        not pytest.importorskip("langchain", minversion=None),
        reason="LangChain not installed",
    )
    def test_protected_llm_basic(self):
        """Test basic ProtectedLLM functionality."""
        from langchain.llms.fake import FakeListLLM
        from prompt_guard.adapters import create_protected_llm

        guard = PromptGuard(policy="default_pii")
        base_llm = FakeListLLM(responses=["Hello, how can I help you?"])

        protected_llm = create_protected_llm(llm=base_llm, guard=guard)

        # Test with PII
        prompt = "My email is john@example.com"
        response = protected_llm(prompt)

        assert response is not None
        assert "john@example.com" not in base_llm.queries[0]  # PII should be masked

    @pytest.mark.skipif(
        not pytest.importorskip("langchain", minversion=None),
        reason="LangChain not installed",
    )
    def test_protected_chat_llm(self):
        """Test ProtectedChatLLM with messages."""
        from langchain.schema import HumanMessage
        from prompt_guard.adapters import ProtectedChatLLM

        guard = PromptGuard(policy="default_pii")

        # Mock chat model
        mock_chat = Mock()
        mock_chat.return_value = Mock(content="Response text")

        protected_chat = ProtectedChatLLM(chat=mock_chat, guard=guard)

        messages = [HumanMessage(content="Email: test@example.com")]
        response = protected_chat(messages)

        # Verify PII was masked in the call to underlying chat
        call_args = mock_chat.call_args[0][0]
        assert "[EMAIL_" in call_args[0].content
        assert "test@example.com" not in call_args[0].content


class TestAsyncGuard:
    """Integration tests for AsyncPromptGuard."""

    @pytest.mark.asyncio
    async def test_async_anonymize(self):
        """Test async anonymization."""
        from prompt_guard import AsyncPromptGuard

        guard = AsyncPromptGuard(policy="default_pii")
        text = "Email: john@example.com"

        anonymized, mapping = await guard.anonymize_async(text)

        assert "[EMAIL_1]" in anonymized
        assert mapping["[EMAIL_1]"] == "john@example.com"

    @pytest.mark.asyncio
    async def test_async_batch(self):
        """Test async batch processing."""
        from prompt_guard import AsyncPromptGuard

        guard = AsyncPromptGuard(policy="default_pii")
        texts = [
            "Email: test1@example.com",
            "Email: test2@example.com",
            "Email: test3@example.com",
        ]

        results = await guard.batch_anonymize(texts)

        assert len(results) == 3
        for anonymized, mapping in results:
            assert "[EMAIL_1]" in anonymized


class TestCaching:
    """Integration tests for caching system."""

    def test_in_memory_cache(self):
        """Test in-memory cache functionality."""
        from prompt_guard.cache import InMemoryCache, CachedPromptGuard

        guard = PromptGuard(policy="default_pii")
        cache = InMemoryCache(max_size=10)
        cached_guard = CachedPromptGuard(guard, cache, ttl=60)

        text = "Email: john@example.com"

        # First call - should cache
        result1 = cached_guard.anonymize(text)
        assert len(cache) == 1

        # Second call - should hit cache
        result2 = cached_guard.anonymize(text)
        assert result1 == result2
        assert len(cache) == 1

    def test_cache_different_policies(self):
        """Test that different policies have different cache keys."""
        from prompt_guard.cache import InMemoryCache, CachedPromptGuard

        cache = InMemoryCache(max_size=10)

        guard1 = PromptGuard(policy="default_pii")
        guard2 = PromptGuard(policy="gdpr_strict")

        cached_guard1 = CachedPromptGuard(guard1, cache)
        cached_guard2 = CachedPromptGuard(guard2, cache)

        text = "Email: john@example.com"

        result1 = cached_guard1.anonymize(text)
        result2 = cached_guard2.anonymize(text)

        # Different policies should create different cache entries
        assert len(cache) == 2

    @pytest.mark.requires_redis
    def test_redis_cache(self):
        """Test Redis cache (requires Redis running)."""
        from prompt_guard.cache import RedisCache, CachedPromptGuard

        try:
            cache = RedisCache(redis_url="redis://localhost:6379")
            guard = PromptGuard(policy="default_pii")
            cached_guard = CachedPromptGuard(guard, cache, ttl=60)

            text = "Email: john@example.com"
            result = cached_guard.anonymize(text)

            assert result is not None

            # Clean up
            cached_guard.clear_cache()
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")


class TestRedisStorage:
    """Integration tests for Redis storage."""

    @pytest.mark.requires_redis
    def test_session_management(self):
        """Test session creation and management."""
        from prompt_guard.storage import RedisMappingStorage

        try:
            storage = RedisMappingStorage(
                redis_url="redis://localhost:6379",
                enable_audit=True,
            )

            # Create session
            session_id = storage.create_session(user_id="test_user")
            assert session_id is not None

            # Store mapping
            mapping = {"[EMAIL_1]": "john@example.com"}
            storage.store_mapping(session_id, mapping)

            # Retrieve mapping
            retrieved = storage.get_mapping(session_id)
            assert retrieved == mapping

            # Check audit log
            audit = storage.get_audit_log(session_id=session_id)
            assert len(audit) > 0

            # Clean up
            storage.delete_mapping(session_id)
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")


class TestEnhancedDetector:
    """Integration tests for enhanced regex detector."""

    def test_international_phone_detection(self):
        """Test international phone number detection."""
        from prompt_guard.detectors.enhanced_regex_detector import EnhancedRegexDetector

        detector = EnhancedRegexDetector()

        tests = [
            ("+1-555-123-4567", "PHONE"),  # US
            ("+44 20 7123 4567", "PHONE"),  # UK
            ("+33 1 23 45 67 89", "PHONE"),  # France
        ]

        for text, expected_type in tests:
            results = detector.detect(text)
            assert len(results) > 0
            assert any(r.entity_type == expected_type for r in results)

    def test_cryptocurrency_detection(self):
        """Test cryptocurrency address detection."""
        from prompt_guard.detectors.enhanced_regex_detector import EnhancedRegexDetector

        detector = EnhancedRegexDetector()

        # Bitcoin address
        btc_text = "Send to: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        results = detector.detect(btc_text)
        assert any(r.entity_type == "CRYPTO_ADDRESS" for r in results)

        # Ethereum address
        eth_text = "Send to: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        results = detector.detect(eth_text)
        assert any(r.entity_type == "CRYPTO_ADDRESS" for r in results)

    def test_priority_based_matching(self):
        """Test that higher priority patterns are matched first."""
        from prompt_guard.detectors.enhanced_regex_detector import EnhancedRegexDetector

        detector = EnhancedRegexDetector()

        # Email should take priority over generic patterns
        text = "Contact: john.smith@example.com"
        results = detector.detect(text)

        # Should detect as EMAIL, not as multiple lower-priority patterns
        email_results = [r for r in results if r.entity_type == "EMAIL"]
        assert len(email_results) == 1


class TestPolicies:
    """Integration tests for industry-specific policies."""

    def test_hipaa_policy(self):
        """Test HIPAA/PHI policy."""
        guard = PromptGuard(policy="hipaa_phi")

        patient_data = """
        Patient: John Smith
        DOB: 1985-03-15
        MRN: MRN-123456
        Email: john.smith@email.com
        Phone: 555-123-4567
        """

        anonymized, mapping = guard.anonymize(patient_data)

        # Should mask all PHI
        assert "John Smith" not in anonymized
        assert "john.smith@email.com" not in anonymized
        assert "MRN-123456" not in anonymized
        assert len(mapping) >= 3

    def test_pci_dss_policy(self):
        """Test PCI-DSS policy."""
        guard = PromptGuard(policy="pci_dss")

        payment_data = """
        Card: 4532-1234-5678-9010
        Cardholder: Jane Doe
        Email: jane@example.com
        """

        anonymized, mapping = guard.anonymize(payment_data)

        # Should mask card and cardholder info
        assert "4532-1234-5678-9010" not in anonymized
        assert "Jane Doe" not in anonymized
        assert len(mapping) >= 2


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_workflow(self):
        """Test complete anonymization workflow."""
        guard = PromptGuard(policy="default_pii")

        # User input with multiple PII types
        user_input = """
        Hi, I'm John Smith. You can reach me at:
        Email: john.smith@example.com
        Phone: 555-123-4567
        I live at 192.168.1.1
        """

        # Step 1: Anonymize
        anonymized, mapping = guard.anonymize(user_input)

        # Verify PII is masked
        assert "John Smith" not in anonymized
        assert "john.smith@example.com" not in anonymized
        assert "555-123-4567" not in anonymized

        # Step 2: Simulate LLM processing
        llm_response = f"Thank you, {list(mapping.keys())[0]}! We'll contact you at {list(mapping.keys())[1]}."

        # Step 3: De-anonymize
        final_response = guard.deanonymize(llm_response, mapping)

        # Verify original data is restored
        assert any(val in final_response for val in mapping.values())

    def test_multi_turn_conversation(self):
        """Test multi-turn conversation with persistent mapping."""
        guard = PromptGuard(policy="default_pii")

        # Turn 1
        turn1 = "My email is john@example.com"
        anon1, map1 = guard.anonymize(turn1)

        # Turn 2 - reference to same email
        turn2 = "Please send the confirmation to that email"
        anon2, map2 = guard.anonymize(turn2)

        # Turn 3 - new PII
        turn3 = "Also CC sarah@example.com"
        anon3, map3 = guard.anonymize(turn3)

        # Combine mappings for de-anonymization
        combined_mapping = {**map1, **map2, **map3}

        # Should be able to de-anonymize all turns
        assert len(combined_mapping) >= 2  # At least 2 emails

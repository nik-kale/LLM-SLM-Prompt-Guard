"""
Performance benchmarks for prompt-guard.

Run with: pytest tests/performance/ --benchmark-only
"""

import pytest
from prompt_guard import PromptGuard, AsyncPromptGuard
import asyncio


class TestDetectorPerformance:
    """Benchmark detector performance."""

    def test_regex_detector_small_text(self, benchmark):
        """Benchmark regex detector on small text."""
        guard = PromptGuard(detectors=["regex"])
        text = "Email: john@example.com, Phone: 555-123-4567"

        result = benchmark(guard.anonymize, text)
        assert result[0] is not None

    def test_regex_detector_medium_text(self, benchmark):
        """Benchmark regex detector on medium text (500 words)."""
        guard = PromptGuard(detectors=["regex"])
        text = (
            "Email: john@example.com, Phone: 555-123-4567. " * 100
        )  # ~500 words

        result = benchmark(guard.anonymize, text)
        assert result[0] is not None

    def test_regex_detector_large_text(self, benchmark):
        """Benchmark regex detector on large text (5000 words)."""
        guard = PromptGuard(detectors=["regex"])
        text = (
            "Email: john@example.com, Phone: 555-123-4567. " * 1000
        )  # ~5000 words

        result = benchmark(guard.anonymize, text)
        assert result[0] is not None

    def test_enhanced_regex_detector(self, benchmark):
        """Benchmark enhanced regex detector."""
        try:
            from prompt_guard.detectors.enhanced_regex_detector import (
                EnhancedRegexDetector,
            )

            guard = PromptGuard(detectors=[])
            guard.detectors = [EnhancedRegexDetector()]
            text = "Email: john@example.com, Phone: +1-555-123-4567, BTC: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

            result = benchmark(guard.anonymize, text)
            assert result[0] is not None
        except ImportError:
            pytest.skip("Enhanced regex detector not available")


class TestCachingPerformance:
    """Benchmark caching performance."""

    def test_without_cache(self, benchmark):
        """Baseline: anonymization without cache."""
        guard = PromptGuard()
        text = "Email: john@example.com"

        result = benchmark(guard.anonymize, text)
        assert result[0] is not None

    def test_with_in_memory_cache_hit(self, benchmark):
        """Benchmark in-memory cache hit."""
        from prompt_guard.cache import InMemoryCache, CachedPromptGuard

        guard = PromptGuard()
        cache = InMemoryCache()
        cached_guard = CachedPromptGuard(guard, cache)

        text = "Email: john@example.com"
        # Prime the cache
        cached_guard.anonymize(text)

        # Benchmark cache hit
        result = benchmark(cached_guard.anonymize, text)
        assert result[0] is not None

    def test_with_in_memory_cache_miss(self, benchmark):
        """Benchmark in-memory cache miss."""
        from prompt_guard.cache import InMemoryCache, CachedPromptGuard

        guard = PromptGuard()
        cache = InMemoryCache()
        cached_guard = CachedPromptGuard(guard, cache)

        # Different text each time to ensure cache miss
        texts = [f"Email: user{i}@example.com" for i in range(1000)]
        counter = {"i": 0}

        def anonymize_with_miss():
            text = texts[counter["i"] % len(texts)]
            counter["i"] += 1
            return cached_guard.anonymize(text)

        result = benchmark(anonymize_with_miss)
        assert result[0] is not None


class TestBatchPerformance:
    """Benchmark batch processing."""

    def test_batch_10_texts(self, benchmark):
        """Benchmark batch processing of 10 texts."""
        guard = PromptGuard()
        texts = [f"Email: user{i}@example.com" for i in range(10)]

        result = benchmark(guard.batch_anonymize, texts)
        assert len(result) == 10

    def test_batch_100_texts(self, benchmark):
        """Benchmark batch processing of 100 texts."""
        guard = PromptGuard()
        texts = [f"Email: user{i}@example.com" for i in range(100)]

        result = benchmark(guard.batch_anonymize, texts)
        assert len(result) == 100

    def test_batch_1000_texts(self, benchmark):
        """Benchmark batch processing of 1000 texts."""
        guard = PromptGuard()
        texts = [f"Email: user{i}@example.com" for i in range(1000)]

        result = benchmark(guard.batch_anonymize, texts)
        assert len(result) == 1000


class TestAsyncPerformance:
    """Benchmark async operations."""

    @pytest.mark.asyncio
    async def test_async_single(self, benchmark):
        """Benchmark single async anonymization."""
        guard = AsyncPromptGuard()
        text = "Email: john@example.com"

        async def async_anonymize():
            return await guard.anonymize_async(text)

        # pytest-benchmark doesn't support async directly
        # So we run it synchronously
        result = benchmark(lambda: asyncio.run(async_anonymize()))
        assert result[0] is not None

    @pytest.mark.asyncio
    async def test_async_batch_10(self, benchmark):
        """Benchmark async batch of 10 texts."""
        guard = AsyncPromptGuard()
        texts = [f"Email: user{i}@example.com" for i in range(10)]

        async def async_batch():
            return await guard.batch_anonymize(texts)

        result = benchmark(lambda: asyncio.run(async_batch()))
        assert len(result) == 10


class TestMemoryUsage:
    """Memory usage tests."""

    def test_memory_baseline(self):
        """Test baseline memory usage."""
        import tracemalloc

        tracemalloc.start()

        guard = PromptGuard()
        text = "Email: john@example.com"

        # Take snapshot before
        snapshot1 = tracemalloc.take_snapshot()

        # Process 1000 texts
        for i in range(1000):
            guard.anonymize(f"Email: user{i}@example.com")

        # Take snapshot after
        snapshot2 = tracemalloc.take_snapshot()

        top_stats = snapshot2.compare_to(snapshot1, "lineno")

        # Get peak memory
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Memory usage should be reasonable (< 50MB for 1000 texts)
        assert peak < 50 * 1024 * 1024  # 50MB

    def test_memory_with_cache(self):
        """Test memory usage with caching."""
        import tracemalloc
        from prompt_guard.cache import InMemoryCache, CachedPromptGuard

        tracemalloc.start()

        guard = PromptGuard()
        cache = InMemoryCache(max_size=100)
        cached_guard = CachedPromptGuard(guard, cache)

        # Process 1000 texts (but only 100 unique)
        for i in range(1000):
            cached_guard.anonymize(f"Email: user{i % 100}@example.com")

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # With cache, memory should be limited
        assert peak < 30 * 1024 * 1024  # 30MB


class TestLatencyDistribution:
    """Test latency distribution."""

    def test_p50_p95_p99_latency(self):
        """Test latency percentiles."""
        import time
        import numpy as np

        guard = PromptGuard()
        text = "Email: john@example.com, Phone: 555-123-4567"

        latencies = []

        # Run 1000 iterations
        for _ in range(1000):
            start = time.perf_counter()
            guard.anonymize(text)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms

        # Calculate percentiles
        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)

        print(f"\nLatency Distribution:")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        print(f"  P99: {p99:.2f}ms")

        # Assert reasonable latencies
        assert p50 < 5.0  # p50 should be < 5ms
        assert p95 < 20.0  # p95 should be < 20ms
        assert p99 < 50.0  # p99 should be < 50ms


class TestThroughput:
    """Test throughput under load."""

    def test_sequential_throughput(self):
        """Test sequential processing throughput."""
        import time

        guard = PromptGuard()
        text = "Email: john@example.com"

        iterations = 10000
        start = time.perf_counter()

        for _ in range(iterations):
            guard.anonymize(text)

        end = time.perf_counter()
        duration = end - start

        throughput = iterations / duration

        print(f"\nSequential Throughput: {throughput:.0f} req/s")

        # Should achieve at least 1000 req/s
        assert throughput > 1000

    @pytest.mark.asyncio
    async def test_concurrent_throughput(self):
        """Test concurrent processing throughput."""
        import time

        guard = AsyncPromptGuard(max_concurrent=100)
        text = "Email: john@example.com"

        iterations = 10000

        async def process_batch():
            tasks = [guard.anonymize_async(text) for _ in range(iterations)]
            return await asyncio.gather(*tasks)

        start = time.perf_counter()
        await process_batch()
        end = time.perf_counter()

        duration = end - start
        throughput = iterations / duration

        print(f"\nConcurrent Throughput: {throughput:.0f} req/s")

        # Concurrent should be much faster
        assert throughput > 5000

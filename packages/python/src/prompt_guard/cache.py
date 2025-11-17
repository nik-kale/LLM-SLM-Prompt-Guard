"""
Caching mechanisms for PromptGuard.

Provides caching to avoid re-processing the same text multiple times.
Supports multiple backend: in-memory, Redis, and custom implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import hashlib
import json
import time
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Represents a cached anonymization result."""
    anonymized: str
    mapping: Dict[str, str]
    timestamp: float
    ttl: Optional[float] = None  # Time to live in seconds

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a value from the cache."""
        pass

    @abstractmethod
    def set(self, key: str, entry: CacheEntry) -> None:
        """Set a value in the cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all entries from the cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a specific entry from the cache."""
        pass


class InMemoryCache(CacheBackend):
    """
    Simple in-memory cache using a dictionary.

    Good for:
    - Single-process applications
    - Development and testing
    - Low-latency requirements

    Not suitable for:
    - Multi-process deployments
    - Shared cache across services
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize in-memory cache.

        Args:
            max_size: Maximum number of entries to cache
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a value from the cache."""
        entry = self.cache.get(key)
        if entry and entry.is_expired():
            del self.cache[key]
            return None
        return entry

    def set(self, key: str, entry: CacheEntry) -> None:
        """Set a value in the cache."""
        # Simple LRU: remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            # Remove the first (oldest) entry
            first_key = next(iter(self.cache))
            del self.cache[first_key]

        self.cache[key] = entry

    def clear(self) -> None:
        """Clear all entries from the cache."""
        self.cache.clear()

    def delete(self, key: str) -> None:
        """Delete a specific entry from the cache."""
        if key in self.cache:
            del self.cache[key]

    def __len__(self) -> int:
        """Return the number of entries in the cache."""
        return len(self.cache)


class RedisCache(CacheBackend):
    """
    Redis-based cache backend.

    Good for:
    - Multi-process deployments
    - Distributed systems
    - Shared cache across services

    Requires:
    - redis-py library
    - Redis server
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        key_prefix: str = "prompt_guard:",
        default_ttl: int = 3600,
    ):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for all cache keys
            default_ttl: Default time-to-live in seconds
        """
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Redis cache requires redis library. "
                "Install it with: pip install redis"
            )

        self.client = redis.from_url(redis_url)
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl

    def _make_key(self, key: str) -> str:
        """Create a prefixed key."""
        return f"{self.key_prefix}{key}"

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a value from the cache."""
        try:
            data = self.client.get(self._make_key(key))
            if data is None:
                return None

            entry_dict = json.loads(data)
            return CacheEntry(**entry_dict)
        except Exception:
            return None

    def set(self, key: str, entry: CacheEntry) -> None:
        """Set a value in the cache."""
        try:
            data = json.dumps({
                "anonymized": entry.anonymized,
                "mapping": entry.mapping,
                "timestamp": entry.timestamp,
                "ttl": entry.ttl,
            })

            ttl = entry.ttl or self.default_ttl
            self.client.setex(
                self._make_key(key),
                int(ttl),
                data
            )
        except Exception:
            pass  # Fail silently on cache errors

    def clear(self) -> None:
        """Clear all entries from the cache."""
        try:
            # Delete all keys with our prefix
            pattern = f"{self.key_prefix}*"
            for key in self.client.scan_iter(match=pattern):
                self.client.delete(key)
        except Exception:
            pass

    def delete(self, key: str) -> None:
        """Delete a specific entry from the cache."""
        try:
            self.client.delete(self._make_key(key))
        except Exception:
            pass


def create_cache_key(text: str, policy: str, detectors: list) -> str:
    """
    Create a deterministic cache key from text and configuration.

    Args:
        text: The text being anonymized
        policy: Policy name
        detectors: List of detector names

    Returns:
        SHA-256 hash as cache key
    """
    # Create a deterministic string representation
    key_data = {
        "text": text,
        "policy": policy,
        "detectors": sorted(detectors),
    }
    key_str = json.dumps(key_data, sort_keys=True)

    # Hash it
    return hashlib.sha256(key_str.encode()).hexdigest()


class CachedPromptGuard:
    """
    Wrapper around PromptGuard that adds caching.

    Example:
        >>> from prompt_guard import PromptGuard
        >>> from prompt_guard.cache import CachedPromptGuard, InMemoryCache
        >>>
        >>> guard = PromptGuard()
        >>> cached_guard = CachedPromptGuard(guard, InMemoryCache())
        >>>
        >>> # First call: processes text
        >>> result1 = cached_guard.anonymize("Email: john@example.com")
        >>>
        >>> # Second call: returns cached result (much faster)
        >>> result2 = cached_guard.anonymize("Email: john@example.com")
    """

    def __init__(
        self,
        guard: Any,
        cache_backend: CacheBackend,
        ttl: Optional[float] = 3600,
    ):
        """
        Initialize cached guard.

        Args:
            guard: PromptGuard instance to wrap
            cache_backend: Cache backend to use
            ttl: Default time-to-live for cache entries in seconds
        """
        self.guard = guard
        self.cache = cache_backend
        self.ttl = ttl

    def anonymize(self, text: str, use_cache: bool = True):
        """
        Anonymize text with caching.

        Args:
            text: Text to anonymize
            use_cache: Whether to use cache

        Returns:
            Tuple of (anonymized_text, mapping)
        """
        if not use_cache:
            return self.guard.anonymize(text)

        # Create cache key
        detector_names = [
            d.__class__.__name__ for d in self.guard.detectors
        ]
        cache_key = create_cache_key(
            text,
            self.guard.policy.get("name", "unknown"),
            detector_names,
        )

        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            return cached.anonymized, cached.mapping

        # Process and cache
        anonymized, mapping = self.guard.anonymize(text)

        entry = CacheEntry(
            anonymized=anonymized,
            mapping=mapping,
            timestamp=time.time(),
            ttl=self.ttl,
        )
        self.cache.set(cache_key, entry)

        return anonymized, mapping

    def deanonymize(self, text: str, mapping: Dict[str, str]) -> str:
        """De-anonymize text (no caching needed)."""
        return self.guard.deanonymize(text, mapping)

    def clear_cache(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()

"""
Tests for the Redis-backed rate limiters, using an in-memory Redis stand-in.
"""

import pytest

pytest.importorskip("redis")

import rate_limiter  # noqa: E402
from rate_limiter import (  # noqa: E402
    GlobalRateLimiter,
    RateLimitConfig,
    RateLimitExceeded,
    TokenBucketRateLimiter,
)


class FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.ops = []

    def __getattr__(self, name):
        def queue(*args, **kwargs):
            self.ops.append((name, args, kwargs))
            return self

        return queue

    def execute(self):
        results = [getattr(self.redis, name)(*args, **kwargs) for name, args, kwargs in self.ops]
        self.ops = []
        return results


class FakeRedis:
    """The subset of redis-py used by the limiters."""

    def __init__(self):
        self.store = {}
        self.ttl = {}

    def pipeline(self, transaction=True):
        return FakePipeline(self)

    def incr(self, key):
        self.store[key] = int(self.store.get(key, 0)) + 1
        return self.store[key]

    def expire(self, key, seconds):
        self.ttl[key] = seconds
        return True

    def get(self, key):
        value = self.store.get(key)
        return None if value is None else str(value).encode()

    def set(self, key, value, ex=None):
        self.store[key] = value
        self.ttl[key] = ex
        return True

    def delete(self, *keys):
        return sum(self.store.pop(key, None) is not None for key in keys)


@pytest.fixture
def clock(monkeypatch):
    now = {"t": 1_000.0}
    monkeypatch.setattr(rate_limiter.time, "time", lambda: now["t"])
    return now


def make_limiter(per_minute=3, per_hour=1000, burst=0, trusted=()):
    redis = FakeRedis()
    config = RateLimitConfig(
        requests_per_minute=per_minute,
        requests_per_hour=per_hour,
        burst_size=burst,
        trusted_ips=set(trusted),
    )
    return TokenBucketRateLimiter(redis, config), redis


class TestTokenBucketRateLimiter:
    def test_rotating_user_id_does_not_bypass_ip_limit(self, clock):
        # The client-supplied X-User-ID used to replace the IP as the key, so
        # a fresh value per request was never limited.
        limiter, _ = make_limiter(per_minute=3)

        for i in range(3):
            limiter.check_rate_limit("203.0.113.7", user_id=f"user-{i}")
        with pytest.raises(RateLimitExceeded) as excinfo:
            limiter.check_rate_limit("203.0.113.7", user_id="user-99")

        assert excinfo.value.limit_type == "minute"

    def test_user_limit_applies_across_ips(self, clock):
        limiter, _ = make_limiter(per_minute=3)

        for i in range(3):
            limiter.check_rate_limit(f"203.0.113.{i}", user_id="alice")
        with pytest.raises(RateLimitExceeded):
            limiter.check_rate_limit("203.0.113.50", user_id="alice")
        limiter.check_rate_limit("203.0.113.50", user_id="bob")

    def test_burst_allowance(self, clock):
        limiter, _ = make_limiter(per_minute=2, burst=2)

        for _ in range(4):
            limiter.check_rate_limit("198.51.100.1")
        with pytest.raises(RateLimitExceeded):
            limiter.check_rate_limit("198.51.100.1")

    def test_window_rollover_and_retry_after(self, clock):
        limiter, _ = make_limiter(per_minute=1)
        clock["t"] = 1_000.0  # minute window [960, 1020)

        limiter.check_rate_limit("198.51.100.2")
        with pytest.raises(RateLimitExceeded) as excinfo:
            limiter.check_rate_limit("198.51.100.2")
        assert excinfo.value.retry_after == 20

        clock["t"] = 1_020.0
        limiter.check_rate_limit("198.51.100.2")

    def test_every_counter_key_expires(self, clock):
        limiter, redis = make_limiter()

        limiter.check_rate_limit("198.51.100.3", user_id="carol")

        assert redis.store
        assert set(redis.ttl) == set(redis.store)
        assert all(0 < ttl <= 3601 for ttl in redis.ttl.values())

    def test_trusted_ip_bypasses_limits(self, clock):
        limiter, redis = make_limiter(per_minute=1, trusted={"10.0.0.1"})

        for _ in range(5):
            limiter.check_rate_limit("10.0.0.1")

        assert redis.store == {}

    def test_get_remaining_and_reset(self, clock):
        limiter, _ = make_limiter(per_minute=5)
        limiter.check_rate_limit("198.51.100.4")
        limiter.check_rate_limit("198.51.100.4")

        assert limiter.get_remaining("198.51.100.4")["minute"] == {
            "limit": 5,
            "used": 2,
            "remaining": 3,
        }

        limiter.reset("198.51.100.4")
        assert limiter.get_remaining("198.51.100.4")["minute"]["used"] == 0


def test_global_limiter_counts_atomically_and_expires(clock):
    redis = FakeRedis()
    limiter = GlobalRateLimiter(redis, max_requests_per_second=2)

    limiter.check_global_limit()
    limiter.check_global_limit()
    with pytest.raises(RateLimitExceeded):
        limiter.check_global_limit()

    assert set(redis.ttl) == set(redis.store)

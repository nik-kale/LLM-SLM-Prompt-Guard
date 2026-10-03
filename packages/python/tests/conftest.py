"""
Shared pytest configuration.
"""

import pytest


def _redis_available() -> bool:
    try:
        import redis

        redis.Redis(host="localhost", port=6379, socket_connect_timeout=0.5).ping()
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    """Skip tests marked requires_redis unless a Redis server is reachable."""
    redis_tests = [item for item in items if "requires_redis" in item.keywords]
    if not redis_tests or _redis_available():
        return
    skip = pytest.mark.skip(reason="Redis server not reachable on localhost:6379")
    for item in redis_tests:
        item.add_marker(skip)

"""
Rate limiting implementation using fixed-window counters with a Redis backend.
"""

import math
import time
import hashlib
from typing import Optional, Set
from dataclasses import dataclass
import redis


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10  # Extra requests allowed on top of each window's limit
    trusted_ips: Set[str] = None  # IPs that bypass rate limiting
    
    def __post_init__(self):
        if self.trusted_ips is None:
            self.trusted_ips = set()


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, retry_after: int, limit_type: str = "minute"):
        self.retry_after = retry_after
        self.limit_type = limit_type
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after} seconds."
        )


class TokenBucketRateLimiter:
    """
    Per-client rate limiter backed by Redis.

    Despite the name, each limit is a fixed-window counter: requests are
    counted per minute and per hour window, and a request is rejected once
    a window's count exceeds its limit plus ``burst_size``. Counting is a
    single atomic INCR per window, so concurrent requests from several proxy
    workers cannot overshoot the limit, and every counter key expires with
    its window.

    Supports:
    - Per-IP rate limiting (always applied, using the connection address)
    - An additional per-user limit when an X-User-ID header is present
    - Trusted IP bypass

    X-User-ID is supplied by the client, so it never replaces the IP limit:
    otherwise a caller could send a new value with every request and never
    be limited. If the proxy runs behind a load balancer, configure the ASGI
    server to take the client address from the trusted forwarding headers
    (e.g. uvicorn ``--proxy-headers --forwarded-allow-ips``), or all clients
    will share the balancer's address.
    """
    
    def __init__(self, redis_client: redis.Redis, config: RateLimitConfig):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Redis client for storing rate limit state
            config: Rate limiting configuration
        """
        self.redis = redis_client
        self.config = config
        
    def _get_key(self, identifier: str, window: str) -> str:
        """
        Generate Redis key prefix for rate limit tracking.
        
        Args:
            identifier: Namespaced identifier, e.g. "ip:10.0.0.1" or "user:alice"
            window: Time window ('minute' or 'hour')
        
        Returns:
            Redis key prefix (the window number is appended per window)
        """
        # Hash the identifier for privacy
        hashed = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        return f"ratelimit:{window}:{hashed}"

    @staticmethod
    def _identifiers(client_ip: str, user_id: Optional[str]) -> list:
        identifiers = [f"ip:{client_ip}"]
        if user_id:
            identifiers.append(f"user:{user_id}")
        return identifiers

    def _windows(self):
        return (
            ("minute", self.config.requests_per_minute, 60),
            ("hour", self.config.requests_per_hour, 3600),
        )
    
    def check_rate_limit(
        self,
        client_ip: str,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Check if request is within rate limits.
        
        Args:
            client_ip: Client IP address
            user_id: Optional user identifier
        
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        # Check if IP is trusted
        if client_ip in self.config.trusted_ips:
            return
        
        for identifier in self._identifiers(client_ip, user_id):
            for window, max_requests, window_seconds in self._windows():
                self._check_window(identifier, window, max_requests, window_seconds)
    
    def _check_window(
        self,
        identifier: str,
        window: str,
        max_requests: int,
        window_seconds: int,
    ) -> None:
        """
        Count this request in the current window and reject it if over the limit.
        
        Args:
            identifier: Namespaced IP or user identifier
            window: Window name ('minute' or 'hour')
            max_requests: Maximum requests allowed in window
            window_seconds: Window duration in seconds
        
        Raises:
            RateLimitExceeded: If limit exceeded
        """
        now = time.time()
        window_index = int(now // window_seconds)
        key = f"{self._get_key(identifier, window)}:{window_index}"

        pipe = self.redis.pipeline(transaction=True)
        pipe.incr(key)
        pipe.expire(key, window_seconds + 1)
        count, _ = pipe.execute()

        if int(count) > max_requests + self.config.burst_size:
            retry_after = max(1, math.ceil((window_index + 1) * window_seconds - now))
            raise RateLimitExceeded(
                retry_after=retry_after,
                limit_type=window,
            )
    
    def get_remaining(
        self,
        client_ip: str,
        user_id: Optional[str] = None,
    ) -> dict:
        """
        Get remaining requests for client.
        
        Args:
            client_ip: Client IP address
            user_id: Optional user identifier
        
        Returns:
            Dictionary with remaining requests per window
        """
        now = time.time()
        status = {}
        for window, max_requests, window_seconds in self._windows():
            window_index = int(now // window_seconds)
            pipe = self.redis.pipeline()
            for identifier in self._identifiers(client_ip, user_id):
                pipe.get(f"{self._get_key(identifier, window)}:{window_index}")
            used = max(int(count) if count else 0 for count in pipe.execute())
            status[window] = {
                "limit": max_requests,
                "used": used,
                "remaining": max(0, max_requests - used),
            }
        return status
    
    def reset(self, identifier: str) -> None:
        """
        Reset rate limit for an identifier (admin function).
        
        Args:
            identifier: IP address or user ID to reset
        """
        now = time.time()
        keys = []
        for window, _, window_seconds in self._windows():
            window_index = int(now // window_seconds)
            for namespaced in (f"ip:{identifier}", f"user:{identifier}"):
                keys.append(f"{self._get_key(namespaced, window)}:{window_index}")
        self.redis.delete(*keys)


class GlobalRateLimiter:
    """
    Global rate limiter to protect against overall system overload.
    
    This limits total requests across all clients.
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        max_requests_per_second: int = 100,
    ):
        """
        Initialize global rate limiter.
        
        Args:
            redis_client: Redis client
            max_requests_per_second: Maximum global requests per second
        """
        self.redis = redis_client
        self.max_requests = max_requests_per_second
    
    def check_global_limit(self) -> None:
        """
        Check global rate limit.
        
        Raises:
            RateLimitExceeded: If global limit exceeded
        """
        key = "ratelimit:global:second"
        current_time = int(time.time())
        
        # Use current second as key
        second_key = f"{key}:{current_time}"
        
        pipe = self.redis.pipeline(transaction=True)
        pipe.incr(second_key)
        pipe.expire(second_key, 2)  # Keep for 2 seconds
        count, _ = pipe.execute()
        
        if int(count) > self.max_requests:
            raise RateLimitExceeded(
                retry_after=1,
                limit_type="global",
            )


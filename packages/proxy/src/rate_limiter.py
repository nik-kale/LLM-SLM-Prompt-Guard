"""
Rate limiting implementation using token bucket algorithm with Redis backend.
"""

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
    burst_size: int = 10  # Allow burst requests
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
    Token bucket rate limiter with Redis backend.
    
    Supports:
    - Per-IP rate limiting
    - Per-user rate limiting (via X-User-ID header)
    - Global rate limiting
    - Burst allowance
    - Trusted IP bypass
    
    The token bucket algorithm works by:
    1. Maintaining a bucket with a maximum capacity of tokens
    2. Tokens are added at a constant rate
    3. Each request consumes one token
    4. If no tokens available, request is rejected
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
        Generate Redis key for rate limit tracking.
        
        Args:
            identifier: IP address or user ID
            window: Time window ('minute' or 'hour')
        
        Returns:
            Redis key
        """
        # Hash the identifier for privacy
        hashed = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        return f"ratelimit:{window}:{hashed}"
    
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
        
        # Determine identifier (prefer user_id over IP)
        identifier = user_id if user_id else client_ip
        
        # Check per-minute limit
        self._check_window(
            identifier,
            "minute",
            self.config.requests_per_minute,
            60,
        )
        
        # Check per-hour limit
        self._check_window(
            identifier,
            "hour",
            self.config.requests_per_hour,
            3600,
        )
    
    def _check_window(
        self,
        identifier: str,
        window: str,
        max_requests: int,
        window_seconds: int,
    ) -> None:
        """
        Check rate limit for a specific time window.
        
        Args:
            identifier: IP or user ID
            window: Window name ('minute' or 'hour')
            max_requests: Maximum requests allowed in window
            window_seconds: Window duration in seconds
        
        Raises:
            RateLimitExceeded: If limit exceeded
        """
        key = self._get_key(identifier, window)
        current_time = time.time()
        
        # Get current request count and window start
        pipe = self.redis.pipeline()
        pipe.get(f"{key}:count")
        pipe.get(f"{key}:start")
        results = pipe.execute()
        
        current_count = int(results[0]) if results[0] else 0
        window_start = float(results[1]) if results[1] else current_time
        
        # Check if window has expired
        if current_time - window_start >= window_seconds:
            # Reset window
            pipe = self.redis.pipeline()
            pipe.set(f"{key}:count", 1, ex=window_seconds)
            pipe.set(f"{key}:start", current_time, ex=window_seconds)
            pipe.execute()
            return
        
        # Check if burst allowance can be used
        if current_count < max_requests + self.config.burst_size:
            # Increment counter
            pipe = self.redis.pipeline()
            pipe.incr(f"{key}:count")
            pipe.expire(f"{key}:count", window_seconds)
            pipe.execute()
            return
        
        # Rate limit exceeded
        time_remaining = int(window_seconds - (current_time - window_start))
        raise RateLimitExceeded(
            retry_after=time_remaining,
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
        identifier = user_id if user_id else client_ip
        
        minute_key = self._get_key(identifier, "minute")
        hour_key = self._get_key(identifier, "hour")
        
        pipe = self.redis.pipeline()
        pipe.get(f"{minute_key}:count")
        pipe.get(f"{hour_key}:count")
        results = pipe.execute()
        
        minute_count = int(results[0]) if results[0] else 0
        hour_count = int(results[1]) if results[1] else 0
        
        return {
            "minute": {
                "limit": self.config.requests_per_minute,
                "used": minute_count,
                "remaining": max(0, self.config.requests_per_minute - minute_count),
            },
            "hour": {
                "limit": self.config.requests_per_hour,
                "used": hour_count,
                "remaining": max(0, self.config.requests_per_hour - hour_count),
            },
        }
    
    def reset(self, identifier: str) -> None:
        """
        Reset rate limit for an identifier (admin function).
        
        Args:
            identifier: IP address or user ID to reset
        """
        for window in ["minute", "hour"]:
            key = self._get_key(identifier, window)
            self.redis.delete(f"{key}:count", f"{key}:start")


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
        
        count = self.redis.incr(second_key)
        self.redis.expire(second_key, 2)  # Keep for 2 seconds
        
        if count > self.max_requests:
            raise RateLimitExceeded(
                retry_after=1,
                limit_type="global",
            )


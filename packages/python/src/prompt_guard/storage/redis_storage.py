"""
Redis-based storage backend for PII mappings.

Provides persistent, distributed storage for PII mappings across
multiple instances and sessions.
"""

from typing import Dict, Optional, List
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available. Install with: pip install redis")


class RedisMappingStorage:
    """
    Redis-based storage for PII mappings.

    Features:
    - Persistent storage across sessions
    - Distributed access across multiple instances
    - Automatic TTL (time-to-live) management
    - Session-based mapping organization
    - Audit trail support

    Example:
        >>> storage = RedisMappingStorage("redis://localhost:6379")
        >>> session_id = storage.create_session("user_123")
        >>> storage.store_mapping(session_id, {"[EMAIL_1]": "john@example.com"})
        >>> mapping = storage.get_mapping(session_id)
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        key_prefix: str = "prompt_guard:",
        default_ttl: int = 86400,  # 24 hours
        enable_audit: bool = True,
    ):
        """
        Initialize Redis storage.

        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for all Redis keys
            default_ttl: Default TTL for mappings in seconds
            enable_audit: Enable audit logging
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis is not installed. Install with: pip install redis"
            )

        self.client: Redis = redis.from_url(redis_url)
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.enable_audit = enable_audit

        # Test connection
        try:
            self.client.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    def _make_key(self, session_id: str, key_type: str = "mapping") -> str:
        """Create a Redis key."""
        return f"{self.key_prefix}{key_type}:{session_id}"

    def create_session(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Create a new session for storing mappings.

        Args:
            user_id: Optional user identifier
            metadata: Additional metadata for the session

        Returns:
            Session ID
        """
        import uuid

        session_id = str(uuid.uuid4())

        # Store session metadata
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        session_key = self._make_key(session_id, "session")
        self.client.setex(
            session_key,
            self.default_ttl,
            json.dumps(session_data),
        )

        # Audit log
        if self.enable_audit:
            self._audit_log("session_created", session_id, {
                "user_id": user_id,
                "metadata": metadata,
            })

        return session_id

    def store_mapping(
        self,
        session_id: str,
        mapping: Dict[str, str],
        ttl: Optional[int] = None,
    ) -> None:
        """
        Store PII mapping for a session.

        Args:
            session_id: Session identifier
            mapping: PII mapping to store
            ttl: Custom TTL in seconds (uses default if None)
        """
        mapping_key = self._make_key(session_id, "mapping")
        ttl = ttl or self.default_ttl

        # Get existing mapping and merge
        existing_data = self.client.get(mapping_key)
        if existing_data:
            existing_mapping = json.loads(existing_data)
            existing_mapping.update(mapping)
            mapping = existing_mapping

        # Store with TTL
        self.client.setex(
            mapping_key,
            ttl,
            json.dumps(mapping),
        )

        # Audit log
        if self.enable_audit:
            self._audit_log("mapping_stored", session_id, {
                "num_entries": len(mapping),
                "ttl": ttl,
            })

    def get_mapping(self, session_id: str) -> Optional[Dict[str, str]]:
        """
        Retrieve PII mapping for a session.

        Args:
            session_id: Session identifier

        Returns:
            PII mapping or None if not found/expired
        """
        mapping_key = self._make_key(session_id, "mapping")
        data = self.client.get(mapping_key)

        if data is None:
            return None

        # Audit log
        if self.enable_audit:
            self._audit_log("mapping_retrieved", session_id, {})

        return json.loads(data)

    def delete_mapping(self, session_id: str) -> bool:
        """
        Delete PII mapping for a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        mapping_key = self._make_key(session_id, "mapping")
        result = self.client.delete(mapping_key) > 0

        if result and self.enable_audit:
            self._audit_log("mapping_deleted", session_id, {})

        return result

    def extend_ttl(self, session_id: str, additional_seconds: int) -> bool:
        """
        Extend the TTL for a mapping.

        Args:
            session_id: Session identifier
            additional_seconds: Seconds to add to current TTL

        Returns:
            True if successful, False otherwise
        """
        mapping_key = self._make_key(session_id, "mapping")
        current_ttl = self.client.ttl(mapping_key)

        if current_ttl < 0:
            return False  # Key doesn't exist or has no expiry

        new_ttl = current_ttl + additional_seconds
        return self.client.expire(mapping_key, new_ttl)

    def list_sessions(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        List active sessions.

        Args:
            user_id: Filter by user ID (None = all sessions)
            limit: Maximum number of sessions to return

        Returns:
            List of session information
        """
        pattern = f"{self.key_prefix}session:*"
        sessions = []

        for key in self.client.scan_iter(match=pattern, count=limit):
            data = self.client.get(key)
            if data:
                session_info = json.loads(data)
                if user_id is None or session_info.get("user_id") == user_id:
                    sessions.append(session_info)

                if len(sessions) >= limit:
                    break

        return sessions

    def _audit_log(
        self,
        event_type: str,
        session_id: str,
        details: Dict,
    ) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            session_id: Session identifier
            details: Event details
        """
        audit_entry = {
            "event_type": event_type,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
        }

        # Store in a list (capped at 10000 entries)
        audit_key = self._make_key("audit", "log")
        self.client.lpush(audit_key, json.dumps(audit_entry))
        self.client.ltrim(audit_key, 0, 9999)  # Keep last 10000 entries

    def get_audit_log(
        self,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        Retrieve audit log entries.

        Args:
            session_id: Filter by session ID (None = all)
            limit: Maximum number of entries to return

        Returns:
            List of audit log entries
        """
        audit_key = self._make_key("audit", "log")
        entries = self.client.lrange(audit_key, 0, limit - 1)

        logs = []
        for entry in entries:
            log_entry = json.loads(entry)
            if session_id is None or log_entry.get("session_id") == session_id:
                logs.append(log_entry)

        return logs

    def health_check(self) -> Dict[str, any]:
        """
        Check Redis connection health.

        Returns:
            Health status information
        """
        try:
            self.client.ping()
            info = self.client.info()

            return {
                "status": "healthy",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def cleanup_expired(self) -> int:
        """
        Clean up expired sessions and mappings.

        Note: Redis handles TTL automatically, but this can be used
        for manual cleanup or monitoring.

        Returns:
            Number of keys cleaned up
        """
        # Redis auto-expires keys, but we can check for orphaned data
        cleaned = 0

        # Find all session keys
        session_pattern = f"{self.key_prefix}session:*"
        for session_key in self.client.scan_iter(match=session_pattern):
            session_id = session_key.decode().split(":")[-1]
            mapping_key = self._make_key(session_id, "mapping")

            # If session exists but mapping doesn't, clean up session
            if not self.client.exists(mapping_key):
                self.client.delete(session_key)
                cleaned += 1

        return cleaned

"""
PostgreSQL-based audit logging and storage.

Provides persistent, ACID-compliant storage for:
- PII mappings
- Audit logs
- Session management
- Compliance reporting
"""

from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2.extras import Json, RealDictCursor
    from psycopg2.pool import SimpleConnectionPool

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logger.warning(
        "PostgreSQL driver not available. Install with: pip install psycopg2-binary"
    )


class PostgresAuditLogger:
    """
    PostgreSQL-based audit logging for PII operations.

    Features:
    - ACID-compliant storage
    - Full audit trail
    - Compliance reporting
    - Advanced querying
    - Retention policies

    Example:
        >>> logger = PostgresAuditLogger(
        ...     connection_string="postgresql://user:pass@localhost/dbname"
        ... )
        >>> logger.initialize_schema()
        >>>
        >>> # Log PII detection
        >>> logger.log_detection(
        ...     session_id="abc123",
        ...     user_id="user_123",
        ...     pii_types=["EMAIL", "PHONE"],
        ...     count=2,
        ... )
        >>>
        >>> # Query audit logs
        >>> logs = logger.get_audit_logs(user_id="user_123", limit=100)
    """

    def __init__(
        self,
        connection_string: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        auto_commit: bool = True,
    ):
        """
        Initialize PostgreSQL audit logger.

        Args:
            connection_string: PostgreSQL connection string
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            auto_commit: Auto-commit transactions
        """
        if not POSTGRES_AVAILABLE:
            raise ImportError(
                "psycopg2 is not installed. "
                "Install it with: pip install psycopg2-binary"
            )

        self.connection_string = connection_string
        self.auto_commit = auto_commit

        # Create connection pool
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=pool_size + max_overflow,
                dsn=connection_string,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}") from e

    def initialize_schema(self) -> None:
        """
        Initialize database schema.

        Creates tables for:
        - Sessions
        - PII mappings
        - Audit logs
        - Detection events
        """
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor()

            # Sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pii_sessions (
                    session_id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMP,
                    metadata JSONB,
                    is_active BOOLEAN DEFAULT TRUE
                )
                """
            )

            # Add index on user_id
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id
                ON pii_sessions(user_id)
                """
            )

            # PII mappings table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pii_mappings (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    placeholder VARCHAR(255) NOT NULL,
                    original_value TEXT NOT NULL,
                    entity_type VARCHAR(100),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    FOREIGN KEY (session_id) REFERENCES pii_sessions(session_id) ON DELETE CASCADE
                )
                """
            )

            # Add indexes
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_mappings_session_id
                ON pii_mappings(session_id)
                """
            )

            # Audit logs table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pii_audit_logs (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(100) NOT NULL,
                    session_id VARCHAR(255),
                    user_id VARCHAR(255),
                    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                    details JSONB,
                    ip_address INET,
                    user_agent TEXT,
                    severity VARCHAR(20) DEFAULT 'INFO'
                )
                """
            )

            # Add indexes for efficient querying
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON pii_audit_logs(timestamp DESC)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_session_id
                ON pii_audit_logs(session_id)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_user_id
                ON pii_audit_logs(user_id)
                """
            )

            # Detection events table (for analytics)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pii_detections (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255),
                    user_id VARCHAR(255),
                    entity_type VARCHAR(100) NOT NULL,
                    count INTEGER DEFAULT 1,
                    confidence FLOAT,
                    detected_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    policy VARCHAR(100)
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_detections_timestamp
                ON pii_detections(detected_at DESC)
                """
            )

            conn.commit()
            logger.info("PostgreSQL schema initialized successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to initialize schema: {e}")
            raise
        finally:
            self.pool.putconn(conn)

    def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        ttl_seconds: int = 86400,
    ) -> str:
        """
        Create a new session.

        Args:
            session_id: Unique session identifier
            user_id: Optional user identifier
            metadata: Optional session metadata
            ttl_seconds: Time-to-live in seconds

        Returns:
            Session ID
        """
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor()

            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

            cursor.execute(
                """
                INSERT INTO pii_sessions (session_id, user_id, expires_at, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (session_id) DO UPDATE
                SET expires_at = EXCLUDED.expires_at
                """,
                (session_id, user_id, expires_at, Json(metadata or {})),
            )

            conn.commit()

            # Log session creation
            self.log_event(
                event_type="session_created",
                session_id=session_id,
                user_id=user_id,
                details={"ttl_seconds": ttl_seconds},
            )

            return session_id

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create session: {e}")
            raise
        finally:
            self.pool.putconn(conn)

    def store_mapping(
        self,
        session_id: str,
        placeholder: str,
        original_value: str,
        entity_type: Optional[str] = None,
    ) -> int:
        """
        Store a PII mapping.

        Args:
            session_id: Session identifier
            placeholder: The placeholder (e.g., "[EMAIL_1]")
            original_value: The original PII value
            entity_type: Type of entity

        Returns:
            Mapping ID
        """
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO pii_mappings (session_id, placeholder, original_value, entity_type)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (session_id, placeholder, original_value, entity_type),
            )

            mapping_id = cursor.fetchone()[0]
            conn.commit()

            return mapping_id

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to store mapping: {e}")
            raise
        finally:
            self.pool.putconn(conn)

    def get_mappings(self, session_id: str) -> Dict[str, str]:
        """
        Retrieve PII mappings for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary of placeholder -> original_value
        """
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute(
                """
                SELECT placeholder, original_value
                FROM pii_mappings
                WHERE session_id = %s
                """,
                (session_id,),
            )

            mappings = {row["placeholder"]: row["original_value"] for row in cursor}

            return mappings

        finally:
            self.pool.putconn(conn)

    def log_event(
        self,
        event_type: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict] = None,
        severity: str = "INFO",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> int:
        """
        Log an audit event.

        Args:
            event_type: Type of event (e.g., "pii_detected", "mapping_accessed")
            session_id: Optional session identifier
            user_id: Optional user identifier
            details: Additional event details
            severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Event ID
        """
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO pii_audit_logs
                (event_type, session_id, user_id, details, severity, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    event_type,
                    session_id,
                    user_id,
                    Json(details or {}),
                    severity,
                    ip_address,
                    user_agent,
                ),
            )

            event_id = cursor.fetchone()[0]
            conn.commit()

            return event_id

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to log event: {e}")
            raise
        finally:
            self.pool.putconn(conn)

    def log_detection(
        self,
        session_id: str,
        user_id: Optional[str],
        pii_types: List[str],
        count: int,
        policy: Optional[str] = None,
    ) -> None:
        """
        Log PII detection event.

        Args:
            session_id: Session identifier
            user_id: User identifier
            pii_types: List of detected PII types
            count: Number of PII instances detected
            policy: Policy used
        """
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor()

            # Log detection event
            for pii_type in set(pii_types):
                cursor.execute(
                    """
                    INSERT INTO pii_detections (session_id, user_id, entity_type, count, policy)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (session_id, user_id, pii_type, count, policy),
                )

            conn.commit()

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to log detection: {e}")
            raise
        finally:
            self.pool.putconn(conn)

    def get_audit_logs(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """
        Query audit logs with filters.

        Args:
            session_id: Filter by session ID
            user_id: Filter by user ID
            event_type: Filter by event type
            start_time: Filter by start time
            end_time: Filter by end time
            severity: Filter by severity
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of audit log entries
        """
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Build query dynamically
            conditions = []
            params = []

            if session_id:
                conditions.append("session_id = %s")
                params.append(session_id)

            if user_id:
                conditions.append("user_id = %s")
                params.append(user_id)

            if event_type:
                conditions.append("event_type = %s")
                params.append(event_type)

            if start_time:
                conditions.append("timestamp >= %s")
                params.append(start_time)

            if end_time:
                conditions.append("timestamp <= %s")
                params.append(end_time)

            if severity:
                conditions.append("severity = %s")
                params.append(severity)

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            query = f"""
                SELECT * FROM pii_audit_logs
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """

            params.extend([limit, offset])

            cursor.execute(query, params)

            return [dict(row) for row in cursor]

        finally:
            self.pool.putconn(conn)

    def get_detection_stats(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get PII detection statistics.

        Args:
            user_id: Filter by user ID
            start_time: Filter by start time
            end_time: Filter by end time

        Returns:
            Statistics dictionary
        """
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            conditions = []
            params = []

            if user_id:
                conditions.append("user_id = %s")
                params.append(user_id)

            if start_time:
                conditions.append("detected_at >= %s")
                params.append(start_time)

            if end_time:
                conditions.append("detected_at <= %s")
                params.append(end_time)

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            # Get total detections
            cursor.execute(
                f"""
                SELECT
                    COUNT(*) as total_detections,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    COUNT(DISTINCT user_id) as unique_users
                FROM pii_detections
                {where_clause}
                """,
                params,
            )

            totals = cursor.fetchone()

            # Get detections by type
            cursor.execute(
                f"""
                SELECT
                    entity_type,
                    COUNT(*) as count,
                    AVG(count) as avg_per_session
                FROM pii_detections
                {where_clause}
                GROUP BY entity_type
                ORDER BY count DESC
                """,
                params,
            )

            by_type = [dict(row) for row in cursor]

            return {
                "total_detections": totals["total_detections"],
                "unique_sessions": totals["unique_sessions"],
                "unique_users": totals["unique_users"],
                "by_type": by_type,
            }

        finally:
            self.pool.putconn(conn)

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions deleted
        """
        conn = self.pool.getconn()
        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM pii_sessions
                WHERE expires_at < NOW() AND is_active = TRUE
                RETURNING session_id
                """
            )

            deleted = cursor.rowcount
            conn.commit()

            logger.info(f"Cleaned up {deleted} expired sessions")

            return deleted

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to cleanup sessions: {e}")
            raise
        finally:
            self.pool.putconn(conn)

    def close(self) -> None:
        """Close all connections in the pool."""
        self.pool.closeall()

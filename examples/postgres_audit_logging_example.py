"""
Example: PostgreSQL-based audit logging for compliance and reporting.

This example demonstrates how to use PostgreSQL for ACID-compliant
audit logging, compliance reporting, and PII mapping persistence.

Installation:
    pip install llm-slm-prompt-guard[postgres]

Setup PostgreSQL:
    docker run -d \
      --name prompt-guard-postgres \
      -e POSTGRES_PASSWORD=postgres \
      -e POSTGRES_DB=prompt_guard \
      -p 5432:5432 \
      postgres:15-alpine

Usage:
    python examples/postgres_audit_logging_example.py
"""

import os
from datetime import datetime, timedelta

# Check if PostgreSQL is available
try:
    from prompt_guard.storage.postgres_storage import PostgresAuditLogger
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("❌ PostgreSQL not installed. Install with: pip install llm-slm-prompt-guard[postgres]")
    exit(1)

from prompt_guard import PromptGuard


def example_1_basic_audit_logging():
    """Example 1: Basic audit logging setup."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Audit Logging")
    print("=" * 60)

    # Connection string
    conn_string = os.getenv(
        "POSTGRES_URL",
        "postgresql://postgres:postgres@localhost:5432/prompt_guard"
    )

    try:
        # Initialize logger
        logger = PostgresAuditLogger(
            connection_string=conn_string,
            pool_size=5,
            auto_commit=True,
        )

        # Initialize database schema
        print("Initializing database schema...")
        logger.initialize_schema()
        print("✓ Schema created successfully")

        # Create a session
        session_id = logger.create_session(
            user_id="user_123",
            metadata={"source": "web_app", "ip": "192.168.1.100"},
            ttl_seconds=3600,  # 1 hour
        )
        print(f"✓ Session created: {session_id}")

        # Store PII mappings
        print("\nStoring PII mappings...")
        mapping_id_1 = logger.store_mapping(
            session_id=session_id,
            placeholder="[EMAIL_1]",
            original_value="john@example.com",
            entity_type="EMAIL",
        )
        print(f"✓ Mapping stored: ID {mapping_id_1}")

        mapping_id_2 = logger.store_mapping(
            session_id=session_id,
            placeholder="[PHONE_1]",
            original_value="555-123-4567",
            entity_type="PHONE",
        )
        print(f"✓ Mapping stored: ID {mapping_id_2}")

        # Retrieve mappings
        mappings = logger.get_mappings(session_id)
        print(f"\nRetrieved mappings: {mappings}")

        # Log events
        print("\nLogging audit events...")
        event_id = logger.log_event(
            event_type="pii_detected",
            session_id=session_id,
            user_id="user_123",
            details={"count": 2, "types": ["EMAIL", "PHONE"]},
            severity="INFO",
        )
        print(f"✓ Event logged: ID {event_id}")

        # Close connection
        logger.close()
        print("\n✓ Basic audit logging completed")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure PostgreSQL is running:")
        print("  docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15-alpine")


def example_2_hipaa_compliance():
    """Example 2: HIPAA-compliant audit logging."""
    print("\n" + "=" * 60)
    print("Example 2: HIPAA Compliance Logging")
    print("=" * 60)

    conn_string = os.getenv(
        "POSTGRES_URL",
        "postgresql://postgres:postgres@localhost:5432/prompt_guard"
    )

    try:
        logger = PostgresAuditLogger(connection_string=conn_string)
        logger.initialize_schema()

        # Create guard with HIPAA policy
        guard = PromptGuard(policy="hipaa_phi")

        # Process patient data
        patient_data = """
        Patient: John Smith
        DOB: 1985-03-15
        MRN: MRN-123456
        Email: john.smith@email.com
        Phone: 555-123-4567
        SSN: 123-45-6789
        """

        print("Processing patient data with HIPAA policy...")
        anonymized, mapping = guard.anonymize(patient_data)

        # Create session for patient interaction
        session_id = logger.create_session(
            user_id="doctor_456",
            metadata={
                "patient_mrn": "MRN-123456",  # Store as metadata, not PII
                "interaction_type": "consultation",
                "department": "cardiology",
            },
            ttl_seconds=7 * 365 * 24 * 3600,  # 7 years for HIPAA
        )

        # Store all PHI mappings
        for placeholder, original in mapping.items():
            logger.store_mapping(
                session_id=session_id,
                placeholder=placeholder,
                original_value=original,
                entity_type=placeholder.split("_")[0].strip("[]"),
            )

        # Log detection event
        logger.log_detection(
            session_id=session_id,
            user_id="doctor_456",
            pii_types=list(set(p.split("_")[0].strip("[]") for p in mapping.keys())),
            count=len(mapping),
            policy="hipaa_phi",
        )

        # Log access event (critical for HIPAA)
        logger.log_event(
            event_type="phi_accessed",
            session_id=session_id,
            user_id="doctor_456",
            details={
                "action": "view_patient_record",
                "patient_identifiers": ["MRN-123456"],
                "reason": "routine_checkup",
            },
            severity="INFO",
            ip_address="10.0.1.50",
            user_agent="EMR System v2.1",
        )

        print(f"\n✓ HIPAA-compliant session created: {session_id}")
        print(f"✓ PHI mappings stored: {len(mapping)}")
        print("✓ Audit trail logged (7-year retention)")

        logger.close()

    except Exception as e:
        print(f"❌ Error: {e}")


def example_3_compliance_reporting():
    """Example 3: Generate compliance reports."""
    print("\n" + "=" * 60)
    print("Example 3: Compliance Reporting")
    print("=" * 60)

    conn_string = os.getenv(
        "POSTGRES_URL",
        "postgresql://postgres:postgres@localhost:5432/prompt_guard"
    )

    try:
        logger = PostgresAuditLogger(connection_string=conn_string)

        # Query audit logs
        print("Querying audit logs for the last 24 hours...")
        logs = logger.get_audit_logs(
            start_time=datetime.utcnow() - timedelta(hours=24),
            end_time=datetime.utcnow(),
            limit=100,
        )

        print(f"\n✓ Found {len(logs)} audit log entries")
        for log in logs[:5]:  # Show first 5
            print(f"  - [{log['timestamp']}] {log['event_type']} (Severity: {log['severity']})")

        # Get detection statistics
        print("\nGetting PII detection statistics...")
        stats = logger.get_detection_stats(
            start_time=datetime.utcnow() - timedelta(days=7),
        )

        print(f"\nDetection Statistics (Last 7 days):")
        print(f"  Total detections: {stats['total_detections']}")
        print(f"  Unique sessions: {stats['unique_sessions']}")
        print(f"  Unique users: {stats['unique_users']}")
        print(f"\n  By entity type:")
        for entity in stats['by_type']:
            print(f"    - {entity['entity_type']}: {entity['count']} "
                  f"(avg {entity['avg_per_session']:.1f} per session)")

        # Filter by user
        print("\nQuerying logs for specific user...")
        user_logs = logger.get_audit_logs(
            user_id="user_123",
            limit=50,
        )
        print(f"✓ Found {len(user_logs)} events for user_123")

        # Filter by event type
        print("\nQuerying PII detection events...")
        detection_logs = logger.get_audit_logs(
            event_type="pii_detected",
            limit=50,
        )
        print(f"✓ Found {len(detection_logs)} PII detection events")

        logger.close()

    except Exception as e:
        print(f"❌ Error: {e}")


def example_4_session_management():
    """Example 4: Session lifecycle management."""
    print("\n" + "=" * 60)
    print("Example 4: Session Management")
    print("=" * 60)

    conn_string = os.getenv(
        "POSTGRES_URL",
        "postgresql://postgres:postgres@localhost:5432/prompt_guard"
    )

    try:
        logger = PostgresAuditLogger(connection_string=conn_string)
        logger.initialize_schema()

        # Create multiple sessions
        print("Creating test sessions...")
        session_ids = []

        for i in range(3):
            session_id = logger.create_session(
                user_id=f"user_{i}",
                metadata={"test": True, "index": i},
                ttl_seconds=10,  # Short TTL for testing
            )
            session_ids.append(session_id)
            print(f"  ✓ Created session {i+1}: {session_id}")

        # Store some mappings
        for session_id in session_ids:
            logger.store_mapping(
                session_id=session_id,
                placeholder="[EMAIL_1]",
                original_value="test@example.com",
                entity_type="EMAIL",
            )

        print(f"\n✓ Created {len(session_ids)} sessions with mappings")

        # Simulate time passing
        print("\nSimulating expiration (waiting 11 seconds)...")
        import time
        time.sleep(11)

        # Clean up expired sessions
        print("Cleaning up expired sessions...")
        deleted_count = logger.cleanup_expired_sessions()
        print(f"✓ Deleted {deleted_count} expired sessions")
        print("  (Note: Cascading delete also removed associated mappings)")

        logger.close()

    except Exception as e:
        print(f"❌ Error: {e}")


def example_5_advanced_queries():
    """Example 5: Advanced querying and analytics."""
    print("\n" + "=" * 60)
    print("Example 5: Advanced Queries")
    print("=" * 60)

    conn_string = os.getenv(
        "POSTGRES_URL",
        "postgresql://postgres:postgres@localhost:5432/prompt_guard"
    )

    try:
        logger = PostgresAuditLogger(connection_string=conn_string)
        logger.initialize_schema()

        # Create test data
        print("Creating test data...")
        guard = PromptGuard(policy="default_pii")

        test_texts = [
            "Email: user1@example.com, Phone: 555-0001",
            "Contact: user2@example.com, SSN: 123-45-6789",
            "Send to user3@example.com or call 555-0003",
        ]

        for i, text in enumerate(test_texts):
            session_id = logger.create_session(
                user_id=f"user_{i % 2}",  # Alternate between 2 users
                metadata={"batch": "test", "index": i},
            )

            anonymized, mapping = guard.anonymize(text)

            # Store mappings
            for placeholder, original in mapping.items():
                logger.store_mapping(
                    session_id=session_id,
                    placeholder=placeholder,
                    original_value=original,
                    entity_type=placeholder.split("_")[0].strip("[]"),
                )

            # Log detection
            pii_types = list(set(p.split("_")[0].strip("[]") for p in mapping.keys()))
            logger.log_detection(
                session_id=session_id,
                user_id=f"user_{i % 2}",
                pii_types=pii_types,
                count=len(mapping),
            )

        print("✓ Test data created")

        # Query by severity
        print("\nQuerying by severity level...")
        info_logs = logger.get_audit_logs(severity="INFO", limit=100)
        print(f"  INFO: {len(info_logs)} events")

        # Query by time range
        print("\nQuerying by time range...")
        recent_logs = logger.get_audit_logs(
            start_time=datetime.utcnow() - timedelta(minutes=5),
            limit=100,
        )
        print(f"  Last 5 minutes: {len(recent_logs)} events")

        # Get statistics by user
        print("\nGetting statistics by user...")
        for user_id in ["user_0", "user_1"]:
            stats = logger.get_detection_stats(user_id=user_id)
            print(f"\n  User {user_id}:")
            print(f"    Total detections: {stats['total_detections']}")
            print(f"    Unique sessions: {stats['unique_sessions']}")

        # Pagination example
        print("\nPagination example (10 per page)...")
        page_size = 10
        for page in range(3):
            logs = logger.get_audit_logs(
                limit=page_size,
                offset=page * page_size,
            )
            print(f"  Page {page + 1}: {len(logs)} results")

        logger.close()
        print("\n✓ Advanced queries completed")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    print("=" * 60)
    print("PostgreSQL Audit Logging Examples")
    print("=" * 60)

    # Check PostgreSQL connection
    conn_string = os.getenv(
        "POSTGRES_URL",
        "postgresql://postgres:postgres@localhost:5432/prompt_guard"
    )
    print(f"\nConnection: {conn_string.replace('postgres:postgres', 'postgres:***')}")

    # Run examples
    try:
        example_1_basic_audit_logging()
        example_2_hipaa_compliance()
        example_3_compliance_reporting()
        example_4_session_management()
        example_5_advanced_queries()

        print("\n" + "=" * 60)
        print("✅ All PostgreSQL audit logging examples completed!")
        print("=" * 60)
        print("\nKey Features Demonstrated:")
        print("  ✓ ACID-compliant audit logging")
        print("  ✓ HIPAA compliance (7-year retention)")
        print("  ✓ Session management with TTL")
        print("  ✓ Advanced querying and filtering")
        print("  ✓ Compliance reporting and analytics")
        print("  ✓ Automatic cleanup of expired data")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

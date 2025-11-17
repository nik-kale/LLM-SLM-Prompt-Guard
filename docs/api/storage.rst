Storage API
===========

This section documents storage backends for persistent PII mappings and audit logging.

Redis Storage
-------------

Redis-based storage for distributed mapping persistence.

.. autoclass:: prompt_guard.storage.redis_storage.RedisMappingStorage
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

PostgreSQL Storage
------------------

PostgreSQL-based audit logging and compliance reporting.

.. autoclass:: prompt_guard.storage.postgres_storage.PostgresAuditLogger
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

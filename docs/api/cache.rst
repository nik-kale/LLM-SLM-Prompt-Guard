Cache API
=========

This section documents caching mechanisms for improved performance.

Cache Backend
-------------

Base class for cache backends.

.. autoclass:: prompt_guard.cache.CacheBackend
   :members:
   :undoc-members:
   :show-inheritance:

In-Memory Cache
---------------

LRU-based in-memory cache.

.. autoclass:: prompt_guard.cache.InMemoryCache
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Redis Cache
-----------

Distributed Redis-based cache.

.. autoclass:: prompt_guard.cache.RedisCache
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Cached Prompt Guard
-------------------

Wrapper that adds caching to any PromptGuard instance.

.. autoclass:: prompt_guard.cache.CachedPromptGuard
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Helper Functions
----------------

.. autofunction:: prompt_guard.cache.create_cache_key

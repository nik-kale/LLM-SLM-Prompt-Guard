Core API
========

This section documents the core components of llm-slm-prompt-guard.

PromptGuard
-----------

The main class for PII anonymization and de-anonymization.

.. autoclass:: prompt_guard.PromptGuard
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

AsyncPromptGuard
----------------

Async version of PromptGuard for high-concurrency applications.

.. autoclass:: prompt_guard.AsyncPromptGuard
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Helper Functions
----------------

.. autofunction:: prompt_guard.create_async_guard

.. autofunction:: prompt_guard.get_version

.. autofunction:: prompt_guard.list_policies

.. autofunction:: prompt_guard.list_detectors

.. autofunction:: prompt_guard.list_storage_backends

.. autofunction:: prompt_guard.list_adapters

Adapters API
============

This section documents framework adapters for integration with popular AI libraries.

LangChain Adapter
-----------------

Integration with LangChain framework.

.. autoclass:: prompt_guard.adapters.langchain_adapter.ProtectedLLM
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: prompt_guard.adapters.langchain_adapter.ProtectedChatLLM
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autofunction:: prompt_guard.adapters.langchain_adapter.create_protected_llm

.. autofunction:: prompt_guard.adapters.langchain_adapter.create_protected_chat

LlamaIndex Adapter
------------------

Integration with LlamaIndex framework for RAG applications.

.. autoclass:: prompt_guard.adapters.llamaindex_adapter.ProtectedQueryEngine
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: prompt_guard.adapters.llamaindex_adapter.ProtectedChatEngine
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autofunction:: prompt_guard.adapters.llamaindex_adapter.create_protected_query_engine

.. autofunction:: prompt_guard.adapters.llamaindex_adapter.create_protected_chat_engine

Hugging Face Adapter
--------------------

Integration with Hugging Face Transformers.

.. autoclass:: prompt_guard.adapters.huggingface_adapter.ProtectedPipeline
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: prompt_guard.adapters.huggingface_adapter.ProtectedConversational
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: prompt_guard.adapters.huggingface_adapter.ProtectedTextGeneration
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autofunction:: prompt_guard.adapters.huggingface_adapter.create_protected_pipeline

.. autofunction:: prompt_guard.adapters.huggingface_adapter.create_protected_conversational

.. autofunction:: prompt_guard.adapters.huggingface_adapter.create_protected_text_generation

Vercel AI SDK Adapter
---------------------

Integration with Vercel AI SDK.

.. autoclass:: prompt_guard.adapters.vercel_ai_adapter.VercelAIAdapter
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: prompt_guard.adapters.vercel_ai_adapter.ProtectedStreamingChat
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autofunction:: prompt_guard.adapters.vercel_ai_adapter.create_protected_vercel_handler

.. autofunction:: prompt_guard.adapters.vercel_ai_adapter.create_protected_streaming_chat

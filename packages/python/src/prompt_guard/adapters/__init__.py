"""
Framework adapters for PromptGuard.

The factory functions are always importable and raise ``ImportError`` when the
framework they wrap is not installed. The wrapper classes for LangChain and
LlamaIndex are only defined when those frameworks are installed.
"""

from .huggingface_adapter import (
    ProtectedConversational,
    ProtectedPipeline,
    ProtectedTextGeneration,
    create_protected_conversational,
    create_protected_pipeline,
    create_protected_text_generation,
)
from .langchain_adapter import create_protected_chat, create_protected_llm
from .llamaindex_adapter import create_protected_chat_engine, create_protected_query_engine
from .vercel_ai_adapter import (
    ProtectedStreamingChat,
    VercelAIAdapter,
    create_protected_streaming_chat,
    create_protected_vercel_handler,
)

__all__ = [
    "ProtectedConversational",
    "ProtectedPipeline",
    "ProtectedStreamingChat",
    "ProtectedTextGeneration",
    "VercelAIAdapter",
    "create_protected_chat",
    "create_protected_chat_engine",
    "create_protected_conversational",
    "create_protected_llm",
    "create_protected_pipeline",
    "create_protected_query_engine",
    "create_protected_streaming_chat",
    "create_protected_text_generation",
    "create_protected_vercel_handler",
]

try:
    from .langchain_adapter import ProtectedChatLLM, ProtectedLLM  # noqa: F401

    __all__ += ["ProtectedChatLLM", "ProtectedLLM"]
except ImportError:
    pass

try:
    from .llamaindex_adapter import ProtectedChatEngine, ProtectedQueryEngine  # noqa: F401

    __all__ += ["ProtectedChatEngine", "ProtectedQueryEngine"]
except ImportError:
    pass

"""
llm-slm-prompt-guard: Enterprise-grade PII protection for LLM/SLM applications.

This package provides policy-driven PII anonymization and de-anonymization
for Large Language Model (LLM) and Small Language Model (SLM) applications.
"""

# Core components
from .guard import PromptGuard
from .async_guard import AsyncPromptGuard, create_async_guard
from .types import (
    DetectorResult,
    AnonymizeResult,
    Mapping,
    AnonymizeOptions,
    DetectionReport,
    RiskLevel,
    OverlapStrategy,
)

# Report generation
from .report import (
    generate_detection_report,
    format_report_text,
    format_report_html,
)

# Logging
from .logging import (
    StructuredLogger,
    JSONFormatter,
    configure_logging,
    get_logger,
)

# Telemetry
from .telemetry import (
    Telemetry,
    TelemetryConfig,
    configure_telemetry,
    get_telemetry,
    is_telemetry_available,
)

# Detectors
from .detectors import BaseDetector, RegexDetector

# Optional detectors
try:
    from .detectors.presidio_detector import PresidioDetector
    _PRESIDIO_AVAILABLE = True
except ImportError:
    _PRESIDIO_AVAILABLE = False

try:
    from .detectors.enhanced_regex_detector import EnhancedRegexDetector
    _ENHANCED_REGEX_AVAILABLE = True
except ImportError:
    _ENHANCED_REGEX_AVAILABLE = False

try:
    from .detectors.spacy_detector import SpacyDetector
    _SPACY_AVAILABLE = True
except ImportError:
    _SPACY_AVAILABLE = False

# Caching
from .cache import (
    CacheBackend,
    InMemoryCache,
    RedisCache,
    CachedPromptGuard,
    create_cache_key,
)

# Storage (optional)
try:
    from .storage.redis_storage import RedisMappingStorage
    _REDIS_STORAGE_AVAILABLE = True
except ImportError:
    _REDIS_STORAGE_AVAILABLE = False

try:
    from .storage.postgres_storage import PostgresAuditLogger
    _POSTGRES_STORAGE_AVAILABLE = True
except ImportError:
    _POSTGRES_STORAGE_AVAILABLE = False

# Adapters (optional)
try:
    from .adapters.langchain_adapter import (
        ProtectedLLM,
        ProtectedChatLLM,
        create_protected_llm,
        create_protected_chat,
    )
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False

try:
    from .adapters.llamaindex_adapter import (
        ProtectedQueryEngine,
        ProtectedChatEngine,
        create_protected_query_engine,
        create_protected_chat_engine,
    )
    _LLAMAINDEX_AVAILABLE = True
except ImportError:
    _LLAMAINDEX_AVAILABLE = False

try:
    from .adapters.vercel_ai_adapter import (
        VercelAIAdapter,
        ProtectedStreamingChat,
        create_protected_vercel_handler,
        create_protected_streaming_chat,
    )
    _VERCEL_AI_AVAILABLE = True
except ImportError:
    _VERCEL_AI_AVAILABLE = False

try:
    from .adapters.huggingface_adapter import (
        ProtectedPipeline,
        ProtectedConversational,
        ProtectedTextGeneration,
        create_protected_pipeline,
        create_protected_conversational,
        create_protected_text_generation,
    )
    _HUGGINGFACE_AVAILABLE = True
except ImportError:
    _HUGGINGFACE_AVAILABLE = False

__version__ = "1.1.0"
__author__ = "LLM-SLM-Prompt-Guard Contributors"
__license__ = "MIT"

# Core exports
__all__ = [
    # Core classes
    "PromptGuard",
    "AsyncPromptGuard",
    "create_async_guard",
    # Types
    "DetectorResult",
    "AnonymizeResult",
    "Mapping",
    "AnonymizeOptions",
    "DetectionReport",
    "RiskLevel",
    "OverlapStrategy",
    # Detectors
    "BaseDetector",
    "RegexDetector",
    # Caching
    "CacheBackend",
    "InMemoryCache",
    "RedisCache",
    "CachedPromptGuard",
    "create_cache_key",
    # Reporting
    "generate_detection_report",
    "format_report_text",
    "format_report_html",
    # Logging
    "StructuredLogger",
    "JSONFormatter",
    "configure_logging",
    "get_logger",
    # Telemetry
    "Telemetry",
    "TelemetryConfig",
    "configure_telemetry",
    "get_telemetry",
    "is_telemetry_available",
]

# Optional exports
if _PRESIDIO_AVAILABLE:
    __all__.extend(["PresidioDetector"])

if _ENHANCED_REGEX_AVAILABLE:
    __all__.extend(["EnhancedRegexDetector"])

if _SPACY_AVAILABLE:
    __all__.extend(["SpacyDetector"])

if _REDIS_STORAGE_AVAILABLE:
    __all__.extend(["RedisMappingStorage"])

if _POSTGRES_STORAGE_AVAILABLE:
    __all__.extend(["PostgresAuditLogger"])

if _LANGCHAIN_AVAILABLE:
    __all__.extend([
        "ProtectedLLM",
        "ProtectedChatLLM",
        "create_protected_llm",
        "create_protected_chat",
    ])

if _LLAMAINDEX_AVAILABLE:
    __all__.extend([
        "ProtectedQueryEngine",
        "ProtectedChatEngine",
        "create_protected_query_engine",
        "create_protected_chat_engine",
    ])

if _VERCEL_AI_AVAILABLE:
    __all__.extend([
        "VercelAIAdapter",
        "ProtectedStreamingChat",
        "create_protected_vercel_handler",
        "create_protected_streaming_chat",
    ])

if _HUGGINGFACE_AVAILABLE:
    __all__.extend([
        "ProtectedPipeline",
        "ProtectedConversational",
        "ProtectedTextGeneration",
        "create_protected_pipeline",
        "create_protected_conversational",
        "create_protected_text_generation",
    ])


def get_version() -> str:
    """Get the installed version."""
    return __version__


def list_policies() -> list[str]:
    """List available built-in policies."""
    import pathlib
    policies_dir = pathlib.Path(__file__).parent / "policies"
    return [p.stem for p in policies_dir.glob("*.yaml")]


def list_detectors() -> dict[str, bool]:
    """List available detectors and their availability."""
    return {
        "regex": True,
        "enhanced_regex": _ENHANCED_REGEX_AVAILABLE,
        "presidio": _PRESIDIO_AVAILABLE,
        "spacy": _SPACY_AVAILABLE,
    }


def list_storage_backends() -> dict[str, bool]:
    """List available storage backends and their availability."""
    return {
        "redis": _REDIS_STORAGE_AVAILABLE,
        "postgres": _POSTGRES_STORAGE_AVAILABLE,
    }


def list_adapters() -> dict[str, bool]:
    """List available framework adapters and their availability."""
    return {
        "langchain": _LANGCHAIN_AVAILABLE,
        "llamaindex": _LLAMAINDEX_AVAILABLE,
        "vercel_ai": _VERCEL_AI_AVAILABLE,
        "huggingface": _HUGGINGFACE_AVAILABLE,
    }

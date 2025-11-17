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

__version__ = "1.0.0"
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
    # Detectors
    "BaseDetector",
    "RegexDetector",
    # Caching
    "CacheBackend",
    "InMemoryCache",
    "RedisCache",
    "CachedPromptGuard",
    "create_cache_key",
]

# Optional exports
if _PRESIDIO_AVAILABLE:
    __all__.extend(["PresidioDetector"])

if _ENHANCED_REGEX_AVAILABLE:
    __all__.extend(["EnhancedRegexDetector"])

if _REDIS_STORAGE_AVAILABLE:
    __all__.extend(["RedisMappingStorage"])

if _LANGCHAIN_AVAILABLE:
    __all__.extend([
        "ProtectedLLM",
        "ProtectedChatLLM",
        "create_protected_llm",
        "create_protected_chat",
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
    }

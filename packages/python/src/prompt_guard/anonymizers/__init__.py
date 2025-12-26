"""
Anonymization strategies for PII replacement.
"""

from .base import AnonymizationStrategy, BaseAnonymizer

try:
    from .synthetic import SyntheticAnonymizer
    SYNTHETIC_AVAILABLE = True
except ImportError:
    SYNTHETIC_AVAILABLE = False

__all__ = [
    "AnonymizationStrategy",
    "BaseAnonymizer",
]

if SYNTHETIC_AVAILABLE:
    __all__.append("SyntheticAnonymizer")


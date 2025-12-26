"""
Anonymization strategies for PII replacement.
"""

from .base import AnonymizationStrategy, BaseAnonymizer
from .hash import HashAnonymizer
from .mask import MaskAnonymizer

try:
    from .synthetic import SyntheticAnonymizer
    SYNTHETIC_AVAILABLE = True
except ImportError:
    SYNTHETIC_AVAILABLE = False

try:
    from .encrypt import EncryptAnonymizer
    ENCRYPT_AVAILABLE = True
except ImportError:
    ENCRYPT_AVAILABLE = False

__all__ = [
    "AnonymizationStrategy",
    "BaseAnonymizer",
    "HashAnonymizer",
    "MaskAnonymizer",
]

if SYNTHETIC_AVAILABLE:
    __all__.append("SyntheticAnonymizer")

if ENCRYPT_AVAILABLE:
    __all__.append("EncryptAnonymizer")


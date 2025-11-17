from .base import BaseDetector
from .regex_detector import RegexDetector

# Optional detectors
try:
    from .presidio_detector import PresidioDetector
    __all__ = ["BaseDetector", "RegexDetector", "PresidioDetector"]
except ImportError:
    __all__ = ["BaseDetector", "RegexDetector"]

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional

@dataclass
class DetectorResult:
    """Represents a detected PII entity in text."""
    entity_type: str
    start: int
    end: int
    text: str
    confidence: Optional[float] = None  # Confidence score (0.0-1.0) for ML-based detectors

Mapping = Dict[str, str]  # placeholder -> original
AnonymizeResult = Tuple[str, Mapping]

@dataclass
class AnonymizeOptions:
    """Options for anonymization process."""
    use_cache: bool = True
    preserve_structure: bool = True  # Keep same length/format when possible
    min_confidence: float = 0.5  # Minimum confidence for ML detectors

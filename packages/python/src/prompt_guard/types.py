from dataclasses import dataclass
from typing import Dict, List, Tuple, Any

@dataclass
class DetectorResult:
    """Represents a detected PII entity in text."""
    entity_type: str
    start: int
    end: int
    text: str

Mapping = Dict[str, str]  # placeholder -> original
AnonymizeResult = Tuple[str, Mapping]

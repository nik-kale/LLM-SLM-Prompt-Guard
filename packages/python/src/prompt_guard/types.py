from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional
from enum import Enum

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


class RiskLevel(str, Enum):
    """Risk level classification based on PII types detected."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DetectionReport:
    """
    Comprehensive report of PII detection results.
    
    Used for compliance auditing, debugging, and dry-run analysis
    without performing actual anonymization.
    """
    entities: List[DetectorResult]
    summary: Dict[str, int]  # count per entity type
    coverage: float  # percentage of text that is PII (0.0-1.0)
    risk_score: RiskLevel  # overall risk assessment
    total_chars: int  # total characters in text
    pii_chars: int  # characters identified as PII
    text_preview: str = ""  # optional: first 100 chars of original text
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization."""
        return {
            "entities": [
                {
                    "type": e.entity_type,
                    "text": e.text,
                    "start": e.start,
                    "end": e.end,
                    "confidence": e.confidence,
                }
                for e in self.entities
            ],
            "summary": self.summary,
            "coverage": self.coverage,
            "risk_score": self.risk_score.value,
            "total_chars": self.total_chars,
            "pii_chars": self.pii_chars,
            "text_preview": self.text_preview,
        }

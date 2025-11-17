"""
spaCy NER-based PII detector.

Uses spaCy's Named Entity Recognition for detecting PII.
This is an alternative to Presidio with simpler dependencies.
"""

from typing import List, Optional
import logging

from .base import BaseDetector
from ..types import DetectorResult

logger = logging.getLogger(__name__)

try:
    import spacy
    from spacy.language import Language

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Install with: pip install spacy")


class SpacyDetector(BaseDetector):
    """
    spaCy-based PII detector using Named Entity Recognition.

    Detects:
    - PERSON: Person names
    - ORG: Organization names
    - GPE: Geopolitical entities (cities, countries)
    - LOC: Non-GPE locations
    - DATE: Dates
    - TIME: Times
    - MONEY: Monetary values
    - PERCENT: Percentages
    - CARDINAL: Numerals that don't fit other categories

    Example:
        >>> detector = SpacyDetector(model="en_core_web_sm")
        >>> results = detector.detect("John Smith works at Acme Corp in New York")
        >>> for r in results:
        ...     print(f"{r.entity_type}: {r.text}")
        PERSON: John Smith
        ORG: Acme Corp
        GPE: New York
    """

    # Map spaCy entity labels to our standard types
    ENTITY_MAPPING = {
        "PERSON": "PERSON",
        "ORG": "ORGANIZATION",
        "GPE": "LOCATION",  # Geopolitical entity
        "LOC": "LOCATION",
        "FAC": "FACILITY",  # Buildings, airports, etc.
        "DATE": "DATE_TIME",
        "TIME": "DATE_TIME",
        "MONEY": "MONEY",
        "PERCENT": "PERCENT",
        "CARDINAL": "NUMBER",
        "ORDINAL": "NUMBER",
        "QUANTITY": "QUANTITY",
        "NORP": "NATIONALITY",  # Nationalities, religious/political groups
        "EVENT": "EVENT",
        "WORK_OF_ART": "WORK_OF_ART",
        "LAW": "LAW",
        "LANGUAGE": "LANGUAGE",
        "PRODUCT": "PRODUCT",
    }

    def __init__(
        self,
        model: str = "en_core_web_sm",
        confidence_threshold: float = 0.5,
        entity_types: Optional[List[str]] = None,
        disable_pipes: Optional[List[str]] = None,
    ):
        """
        Initialize spaCy detector.

        Args:
            model: spaCy model name (e.g., "en_core_web_sm", "en_core_web_lg")
            confidence_threshold: Minimum confidence score (not all models support this)
            entity_types: List of entity types to detect (None = all)
            disable_pipes: spaCy pipeline components to disable for performance
        """
        if not SPACY_AVAILABLE:
            raise ImportError(
                "spaCy is not installed. Install it with: pip install spacy"
            )

        self.model_name = model
        self.confidence_threshold = confidence_threshold
        self.entity_types = set(entity_types) if entity_types else None

        # Try to load the model
        try:
            self.nlp: Language = spacy.load(model)
        except OSError as e:
            logger.error(
                f"Failed to load spaCy model '{model}'. "
                f"Download it with: python -m spacy download {model}"
            )
            raise ImportError(
                f"spaCy model '{model}' not found. "
                f"Download with: python -m spacy download {model}"
            ) from e

        # Disable unnecessary pipeline components for performance
        if disable_pipes:
            for pipe in disable_pipes:
                if pipe in self.nlp.pipe_names:
                    self.nlp.disable_pipe(pipe)
        else:
            # Default: disable components not needed for NER
            for pipe in ["tok2vec", "tagger", "parser", "lemmatizer"]:
                if pipe in self.nlp.pipe_names and pipe != "ner":
                    try:
                        self.nlp.disable_pipe(pipe)
                    except:
                        pass

    def detect(self, text: str) -> List[DetectorResult]:
        """
        Detect PII using spaCy NER.

        Args:
            text: Text to analyze

        Returns:
            List of detected PII entities
        """
        results: List[DetectorResult] = []

        try:
            # Process with spaCy
            doc = self.nlp(text)

            # Extract entities
            for ent in doc.ents:
                # Map entity type
                entity_type = self.ENTITY_MAPPING.get(ent.label_, ent.label_)

                # Filter by entity type if specified
                if self.entity_types and entity_type not in self.entity_types:
                    continue

                # Get confidence if available (some models don't provide it)
                confidence = None
                if hasattr(ent, "_") and hasattr(ent._, "confidence"):
                    confidence = ent._.confidence
                else:
                    # Default confidence for spaCy NER
                    confidence = 0.85

                # Filter by confidence
                if confidence and confidence < self.confidence_threshold:
                    continue

                results.append(
                    DetectorResult(
                        entity_type=entity_type,
                        start=ent.start_char,
                        end=ent.end_char,
                        text=ent.text,
                        confidence=confidence,
                    )
                )

        except Exception as e:
            logger.error(f"spaCy detection failed: {e}")

        return results

    @classmethod
    def is_available(cls) -> bool:
        """Check if spaCy is available."""
        return SPACY_AVAILABLE

    @classmethod
    def list_available_models(cls) -> List[str]:
        """List installed spaCy models."""
        if not SPACY_AVAILABLE:
            return []

        try:
            import subprocess
            import json

            result = subprocess.run(
                ["python", "-m", "spacy", "info", "--json"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                info = json.loads(result.stdout)
                return list(info.get("pipelines", {}).keys())
        except Exception as e:
            logger.warning(f"Failed to list spaCy models: {e}")

        return []


# Convenience function
def create_spacy_detector(
    model: str = "en_core_web_sm", **kwargs
) -> SpacyDetector:
    """Create a spaCy detector instance."""
    return SpacyDetector(model=model, **kwargs)

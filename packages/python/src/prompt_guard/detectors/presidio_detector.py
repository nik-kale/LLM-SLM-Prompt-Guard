"""
Microsoft Presidio detector integration.

Presidio is a data protection and de-identification SDK that provides
advanced PII detection using NER (Named Entity Recognition) and pattern matching.

This is an optional detector that requires presidio-analyzer to be installed.
"""

from typing import List, Optional
import logging

from .base import BaseDetector
from ..types import DetectorResult

logger = logging.getLogger(__name__)

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    logger.warning(
        "Presidio not available. Install with: pip install presidio-analyzer"
    )


class PresidioDetector(BaseDetector):
    """
    Microsoft Presidio-based PII detector.

    Provides ML-based entity recognition with support for:
    - PERSON names
    - LOCATION (addresses, cities, countries)
    - ORGANIZATION names
    - EMAIL addresses
    - PHONE numbers
    - CREDIT_CARD numbers
    - SSN (US Social Security Numbers)
    - IBAN (International Bank Account Numbers)
    - And many more...

    Example:
        >>> detector = PresidioDetector(language="en")
        >>> results = detector.detect("John Smith lives in New York")
        >>> for r in results:
        ...     print(f"{r.entity_type}: {r.text}")
        PERSON: John Smith
        LOCATION: New York
    """

    # Map Presidio entity types to our standard types
    ENTITY_TYPE_MAPPING = {
        "PERSON": "PERSON",
        "EMAIL_ADDRESS": "EMAIL",
        "PHONE_NUMBER": "PHONE",
        "CREDIT_CARD": "CREDIT_CARD",
        "US_SSN": "SSN",
        "IP_ADDRESS": "IP_ADDRESS",
        "LOCATION": "LOCATION",
        "DATE_TIME": "DATE_TIME",
        "NRP": "NATIONALITY",  # Nationality/Religious/Political group
        "IBAN_CODE": "IBAN",
        "US_BANK_NUMBER": "BANK_ACCOUNT",
        "US_DRIVER_LICENSE": "DRIVERS_LICENSE",
        "US_PASSPORT": "PASSPORT",
        "CRYPTO": "CRYPTO_ADDRESS",
        "UK_NHS": "NHS_NUMBER",
        "MEDICAL_LICENSE": "MEDICAL_LICENSE",
    }

    def __init__(
        self,
        language: str = "en",
        entities: Optional[List[str]] = None,
        score_threshold: float = 0.5,
        use_recognizer_cache: bool = True,
    ):
        """
        Initialize Presidio detector.

        Args:
            language: Language code (e.g., "en", "es", "de")
            entities: List of entity types to detect. None = all entities.
            score_threshold: Minimum confidence score (0.0-1.0)
            use_recognizer_cache: Whether to cache recognizer results
        """
        if not PRESIDIO_AVAILABLE:
            raise ImportError(
                "Presidio is not installed. "
                "Install it with: pip install presidio-analyzer"
            )

        self.language = language
        self.entities = entities
        self.score_threshold = score_threshold

        # Initialize Presidio analyzer
        try:
            # Create NLP engine configuration
            nlp_configuration = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": language, "model_name": f"{language}_core_web_sm"}],
            }

            # Create NLP engine provider
            provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
            nlp_engine = provider.create_engine()

            # Create analyzer with NLP engine
            self.analyzer = AnalyzerEngine(
                nlp_engine=nlp_engine,
                supported_languages=[language],
            )

        except Exception as e:
            logger.warning(
                f"Failed to initialize Presidio with spaCy. "
                f"Falling back to pattern-based only. Error: {e}"
            )
            # Fallback to pattern-based detection only
            self.analyzer = AnalyzerEngine(supported_languages=[language])

    def detect(self, text: str) -> List[DetectorResult]:
        """
        Detect PII using Presidio analyzer.

        Args:
            text: Text to analyze

        Returns:
            List of detected PII entities
        """
        results: List[DetectorResult] = []

        try:
            # Run Presidio analysis
            presidio_results = self.analyzer.analyze(
                text=text,
                language=self.language,
                entities=self.entities,
                score_threshold=self.score_threshold,
            )

            # Convert Presidio results to our format
            for presidio_result in presidio_results:
                # Map entity type
                entity_type = self.ENTITY_TYPE_MAPPING.get(
                    presidio_result.entity_type, presidio_result.entity_type
                )

                results.append(
                    DetectorResult(
                        entity_type=entity_type,
                        start=presidio_result.start,
                        end=presidio_result.end,
                        text=text[presidio_result.start : presidio_result.end],
                        confidence=presidio_result.score,
                    )
                )

        except Exception as e:
            logger.error(f"Presidio detection failed: {e}")

        return results

    @classmethod
    def is_available(cls) -> bool:
        """Check if Presidio is available."""
        return PRESIDIO_AVAILABLE

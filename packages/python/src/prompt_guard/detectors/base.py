"""
Base detector classes and utilities for building custom PII detectors.

This module provides the foundation for creating custom detectors in the
Prompt Guard ecosystem. It includes:

- BaseDetector: Abstract base class for all detectors
- RegexBasedDetector: Helper class for regex-based detection
- MLBasedDetector: Helper class for ML-based detection
- DetectorRegistry: System for registering and loading custom detectors
- Validation and testing utilities

Example:
    Creating a custom detector::

        from prompt_guard.detectors.base import BaseDetector, DetectorResult

        class MyCustomDetector(BaseDetector):
            '''Detects custom PII patterns.'''

            def detect(self, text: str) -> List[DetectorResult]:
                results = []
                # Your custom detection logic here
                return results

        # Use your detector
        from prompt_guard import PromptGuard
        guard = PromptGuard(detectors=[MyCustomDetector()])
"""

import re
from abc import ABC, abstractmethod
from typing import List, Dict, Pattern, Optional, Callable, Any
from ..types import DetectorResult


class BaseDetector(ABC):
    """
    Abstract base class for all PII detectors.

    All custom detectors must inherit from this class and implement the detect() method.

    Attributes:
        name (str): Human-readable name of the detector
        version (str): Version string for the detector
        supported_languages (List[str]): List of supported language codes

    Example:
        >>> class EmailDetector(BaseDetector):
        ...     def detect(self, text: str) -> List[DetectorResult]:
        ...         # Detection logic
        ...         return []
    """

    def __init__(self, name: str = "", version: str = "1.0.0"):
        """
        Initialize the detector.

        Args:
            name: Human-readable name for the detector
            version: Version string
        """
        self.name = name or self.__class__.__name__
        self.version = version
        self.supported_languages = ["en"]  # Default to English

    @abstractmethod
    def detect(self, text: str) -> List[DetectorResult]:
        """
        Detect PII entities in the given text.

        This method must be implemented by all custom detectors.

        Args:
            text: The text to analyze for PII.

        Returns:
            A list of DetectorResult objects representing detected PII entities.
            Each result should include:
            - entity_type: The type of PII (e.g., "EMAIL", "PHONE")
            - start: Start position in the text
            - end: End position in the text
            - score: Confidence score (0.0 to 1.0)

        Example:
            >>> def detect(self, text: str) -> List[DetectorResult]:
            ...     results = []
            ...     # Find all emails
            ...     for match in re.finditer(r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b', text):
            ...         results.append(DetectorResult(
            ...             entity_type="EMAIL",
            ...             start=match.start(),
            ...             end=match.end(),
            ...             score=1.0
            ...         ))
            ...     return results
        """
        raise NotImplementedError

    def validate_result(self, result: DetectorResult, text: str) -> bool:
        """
        Validate a detection result.

        Args:
            result: The detection result to validate
            text: The original text

        Returns:
            True if the result is valid, False otherwise
        """
        if result.start < 0 or result.end > len(text):
            return False
        if result.start >= result.end:
            return False
        if not 0.0 <= result.score <= 1.0:
            return False
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this detector.

        Returns:
            Dictionary containing detector metadata
        """
        return {
            "name": self.name,
            "version": self.version,
            "supported_languages": self.supported_languages,
            "class": self.__class__.__name__,
        }


class RegexBasedDetector(BaseDetector):
    """
    Helper base class for regex-based detectors.

    This class provides utilities for building detectors that use regular expressions.

    Attributes:
        patterns (Dict[str, Pattern]): Dictionary mapping entity types to compiled regex patterns

    Example:
        >>> class CustomRegexDetector(RegexBasedDetector):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self.add_pattern("CUSTOM_ID", r"ID-\\d{6}")
        ...
        ...     def detect(self, text: str) -> List[DetectorResult]:
        ...         return self.detect_patterns(text)
    """

    def __init__(self, name: str = "", version: str = "1.0.0"):
        """Initialize regex-based detector."""
        super().__init__(name, version)
        self.patterns: Dict[str, Pattern] = {}

    def add_pattern(
        self,
        entity_type: str,
        pattern: str,
        flags: int = re.IGNORECASE,
        validator: Optional[Callable[[str], bool]] = None,
    ) -> None:
        """
        Add a regex pattern for an entity type.

        Args:
            entity_type: The type of entity this pattern detects
            pattern: Regular expression pattern
            flags: Regex flags (default: re.IGNORECASE)
            validator: Optional function to validate matches

        Example:
            >>> detector = RegexBasedDetector()
            >>> detector.add_pattern("SSN", r"\\d{3}-\\d{2}-\\d{4}")
            >>> detector.add_pattern(
            ...     "PHONE",
            ...     r"\\d{3}-\\d{4}",
            ...     validator=lambda x: len(x.replace("-", "")) == 7
            ... )
        """
        self.patterns[entity_type] = {
            "pattern": re.compile(pattern, flags),
            "validator": validator,
        }

    def detect_patterns(self, text: str, confidence: float = 1.0) -> List[DetectorResult]:
        """
        Detect all registered patterns in text.

        Args:
            text: Text to search
            confidence: Default confidence score for matches

        Returns:
            List of detection results
        """
        results = []
        for entity_type, config in self.patterns.items():
            pattern = config["pattern"]
            validator = config.get("validator")

            for match in pattern.finditer(text):
                matched_text = match.group()

                # Apply validator if present
                if validator and not validator(matched_text):
                    continue

                results.append(
                    DetectorResult(
                        entity_type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        text=matched_text,
                        confidence=confidence,
                    )
                )
        return results


class MLBasedDetector(BaseDetector):
    """
    Helper base class for ML-based detectors.

    This class provides utilities for building detectors that use machine learning models.

    Attributes:
        model: The underlying ML model
        threshold (float): Confidence threshold for detections

    Example:
        >>> class CustomMLDetector(MLBasedDetector):
        ...     def __init__(self):
        ...         super().__init__(threshold=0.8)
        ...         self.model = load_my_model()
        ...
        ...     def detect(self, text: str) -> List[DetectorResult]:
        ...         predictions = self.model.predict(text)
        ...         return self.filter_by_threshold(predictions)
    """

    def __init__(
        self, name: str = "", version: str = "1.0.0", threshold: float = 0.5
    ):
        """
        Initialize ML-based detector.

        Args:
            name: Detector name
            version: Detector version
            threshold: Minimum confidence threshold (0.0 to 1.0)
        """
        super().__init__(name, version)
        self.threshold = threshold
        self.model: Optional[Any] = None

    def filter_by_threshold(
        self, results: List[DetectorResult]
    ) -> List[DetectorResult]:
        """
        Filter results by confidence threshold.

        Args:
            results: List of detection results

        Returns:
            Filtered list of results above threshold
        """
        return [r for r in results if (r.confidence or 0.0) >= self.threshold]

    def load_model(self, model_path: str) -> None:
        """
        Load ML model from path.

        Args:
            model_path: Path to the model file

        Note:
            Subclasses should override this method to implement
            their specific model loading logic.
        """
        raise NotImplementedError("Subclasses must implement load_model()")


class DetectorRegistry:
    """
    Registry for managing custom detectors.

    This allows dynamic registration and loading of detector implementations.

    Example:
        >>> registry = DetectorRegistry()
        >>> registry.register("my_detector", MyCustomDetector)
        >>> detector = registry.create("my_detector")
    """

    def __init__(self):
        """Initialize the detector registry."""
        self._detectors: Dict[str, type] = {}

    def register(self, name: str, detector_class: type) -> None:
        """
        Register a detector class.

        Args:
            name: Unique name for the detector
            detector_class: The detector class (must inherit from BaseDetector)

        Raises:
            ValueError: If detector_class doesn't inherit from BaseDetector

        Example:
            >>> registry.register("email", EmailDetector)
        """
        if not issubclass(detector_class, BaseDetector):
            raise ValueError(
                f"Detector class must inherit from BaseDetector, got {detector_class}"
            )
        self._detectors[name] = detector_class

    def create(self, name: str, **kwargs) -> BaseDetector:
        """
        Create a detector instance.

        Args:
            name: Name of the registered detector
            **kwargs: Arguments to pass to detector constructor

        Returns:
            Detector instance

        Raises:
            KeyError: If detector name is not registered

        Example:
            >>> detector = registry.create("email", threshold=0.8)
        """
        if name not in self._detectors:
            raise KeyError(
                f"Detector '{name}' not registered. "
                f"Available: {list(self._detectors.keys())}"
            )
        return self._detectors[name](**kwargs)

    def list_detectors(self) -> List[str]:
        """
        List all registered detector names.

        Returns:
            List of detector names
        """
        return list(self._detectors.keys())

    def get_detector_info(self, name: str) -> Dict[str, Any]:
        """
        Get information about a registered detector.

        Args:
            name: Detector name

        Returns:
            Dictionary with detector information
        """
        if name not in self._detectors:
            raise KeyError(f"Detector '{name}' not registered")

        detector_class = self._detectors[name]
        return {
            "name": name,
            "class": detector_class.__name__,
            "module": detector_class.__module__,
            "doc": detector_class.__doc__,
        }


# Global detector registry
detector_registry = DetectorRegistry()

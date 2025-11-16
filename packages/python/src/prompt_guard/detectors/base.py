from abc import ABC, abstractmethod
from typing import List
from ..types import DetectorResult


class BaseDetector(ABC):
    """Base class for all PII detectors."""

    @abstractmethod
    def detect(self, text: str) -> List[DetectorResult]:
        """
        Detect PII entities in the given text.

        Args:
            text: The text to analyze for PII.

        Returns:
            A list of DetectorResult objects representing detected PII entities.
        """
        raise NotImplementedError

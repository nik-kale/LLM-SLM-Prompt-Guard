"""
Base classes for anonymization strategies.
"""

from enum import Enum
from typing import Dict
from abc import ABC, abstractmethod


class AnonymizationStrategy(str, Enum):
    """Available anonymization strategies."""
    PLACEHOLDER = "placeholder"  # [EMAIL_1], [PERSON_1], etc.
    SYNTHETIC = "synthetic"  # Realistic fake data


class BaseAnonymizer(ABC):
    """
    Base class for anonymization strategies.
    """
    
    @abstractmethod
    def anonymize_entity(
        self,
        entity_type: str,
        original_value: str,
        entity_index: int,
    ) -> str:
        """
        Anonymize a single entity.
        
        Args:
            entity_type: Type of PII entity (e.g., "EMAIL", "PERSON")
            original_value: Original PII value
            entity_index: Index of this entity type in the text
        
        Returns:
            Anonymized value
        """
        pass
    
    @abstractmethod
    def get_mapping(self) -> Dict[str, str]:
        """
        Get the current anonymization mapping.
        
        Returns:
            Dictionary mapping anonymized values to original values
        """
        pass
    
    @abstractmethod
    def reset(self):
        """Reset the anonymizer state."""
        pass


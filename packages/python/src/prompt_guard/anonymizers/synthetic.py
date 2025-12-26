"""
Synthetic data replacement using Faker library.
"""

import hashlib
from typing import Dict, Optional
from .base import BaseAnonymizer

try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False


class SyntheticAnonymizer(BaseAnonymizer):
    """
    Anonymizer that replaces PII with realistic synthetic data.
    
    Uses Faker library to generate:
    - Realistic names
    - Valid email addresses
    - Phone numbers in various formats
    - Addresses
    - Credit card numbers (fake but format-valid)
    - SSNs (fake but format-valid)
    
    Features:
    - Deterministic replacement (same input → same output within session)
    - Locale support for names and addresses
    - Format-preserving where possible
    """
    
    def __init__(self, locale: str = "en_US", seed: Optional[int] = None):
        """
        Initialize synthetic anonymizer.
        
        Args:
            locale: Faker locale for generating data (e.g., "en_US", "fr_FR", "de_DE")
            seed: Random seed for deterministic generation
        """
        if not FAKER_AVAILABLE:
            raise ImportError(
                "Faker library is required for synthetic anonymization. "
                "Install it with: pip install faker"
            )
        
        self.locale = locale
        self.fake = Faker(locale)
        
        if seed is not None:
            Faker.seed(seed)
        
        self._mapping: Dict[str, str] = {}
        self._synthetic_to_original: Dict[str, str] = {}
        self._seen_originals: Dict[str, str] = {}  # original -> synthetic
    
    def anonymize_entity(
        self,
        entity_type: str,
        original_value: str,
        entity_index: int,
    ) -> str:
        """
        Replace entity with synthetic data.
        
        Args:
            entity_type: Type of PII entity
            original_value: Original PII value
            entity_index: Index of this entity type
        
        Returns:
            Synthetic replacement value
        """
        # Check if we've already generated a synthetic value for this original
        if original_value in self._seen_originals:
            return self._seen_originals[original_value]
        
        # Generate deterministic synthetic data
        synthetic_value = self._generate_synthetic(entity_type, original_value, entity_index)
        
        # Store mappings
        self._seen_originals[original_value] = synthetic_value
        self._mapping[synthetic_value] = original_value
        self._synthetic_to_original[synthetic_value] = original_value
        
        return synthetic_value
    
    def _generate_synthetic(
        self,
        entity_type: str,
        original_value: str,
        entity_index: int,
    ) -> str:
        """
        Generate synthetic data for a specific entity type.
        
        Args:
            entity_type: Type of PII entity
            original_value: Original value (for format preservation)
            entity_index: Entity index for seeding
        
        Returns:
            Synthetic value
        """
        # Create deterministic seed from original value
        seed_value = int(hashlib.md5(original_value.encode()).hexdigest()[:8], 16)
        self.fake.seed_instance(seed_value)
        
        # Generate based on entity type
        if entity_type in ("PERSON", "NAME"):
            return self.fake.name()
        
        elif entity_type == "EMAIL":
            return self.fake.email()
        
        elif entity_type in ("PHONE", "PHONE_NUMBER"):
            # Try to preserve format
            if "-" in original_value:
                return self.fake.phone_number()
            else:
                return self.fake.phone_number().replace("-", "")
        
        elif entity_type == "SSN":
            return self.fake.ssn()
        
        elif entity_type == "CREDIT_CARD":
            return self.fake.credit_card_number()
        
        elif entity_type in ("ADDRESS", "LOCATION"):
            return self.fake.address().replace("\n", ", ")
        
        elif entity_type == "CITY":
            return self.fake.city()
        
        elif entity_type == "STATE":
            return self.fake.state()
        
        elif entity_type == "COUNTRY":
            return self.fake.country()
        
        elif entity_type == "ZIP_CODE":
            return self.fake.zipcode()
        
        elif entity_type == "COMPANY":
            return self.fake.company()
        
        elif entity_type == "IP_ADDRESS":
            if ":" in original_value:  # IPv6
                return self.fake.ipv6()
            else:  # IPv4
                return self.fake.ipv4()
        
        elif entity_type == "URL":
            return self.fake.url()
        
        elif entity_type == "USERNAME":
            return self.fake.user_name()
        
        elif entity_type == "DATE":
            return str(self.fake.date())
        
        elif entity_type == "TIME":
            return str(self.fake.time())
        
        else:
            # Fallback: generate a word
            return self.fake.word()
    
    def get_mapping(self) -> Dict[str, str]:
        """
        Get mapping from synthetic to original values.
        
        Returns:
            Dictionary mapping synthetic values to original values
        """
        return self._mapping.copy()
    
    def reset(self):
        """Reset all mappings."""
        self._mapping.clear()
        self._synthetic_to_original.clear()
        self._seen_originals.clear()


"""
Synthetic data replacement using Faker library.
"""

import hashlib
import hmac
import secrets
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
    - Distinct originals always get distinct synthetic values, so the
      mapping can be reversed unambiguously

    The fake value for each original is derived from an HMAC of the original
    under a key. Without a ``seed`` the key is random per instance, so the
    synthetic values sent to a model cannot be linked back to the originals
    by generating fakes for candidate values.
    """

    _MAX_ATTEMPTS = 100
    
    def __init__(self, locale: str = "en_US", seed: Optional[int] = None):
        """
        Initialize synthetic anonymizer.
        
        Args:
            locale: Faker locale for generating data (e.g., "en_US", "fr_FR", "de_DE")
            seed: Seed for reproducible output across instances and processes.
                It acts as the key for deriving fake values, so anyone who
                knows it can test guesses of the original values; keep it
                secret. If omitted, output is only stable within this instance.
        """
        if not FAKER_AVAILABLE:
            raise ImportError(
                "Faker library is required for synthetic anonymization. "
                "Install it with: pip install faker"
            )
        
        self.locale = locale
        self.fake = Faker(locale)
        # Faker.seed() would reseed every Faker instance in the process, so the
        # seed only feeds this instance's key.
        if seed is None:
            self._seed_key = secrets.token_bytes(32)
        else:
            self._seed_key = hashlib.sha256(f"prompt-guard-synthetic:{seed}".encode()).digest()
        
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
        
        # Generate deterministic synthetic data. Retry on collisions: two
        # originals sharing a synthetic value would make the mapping ambiguous.
        synthetic_value = self._generate_synthetic(entity_type, original_value, entity_index)
        attempt = 0
        while synthetic_value in self._mapping or synthetic_value == original_value:
            attempt += 1
            synthetic_value = self._generate_synthetic(
                entity_type, original_value, entity_index, attempt
            )
            if attempt > self._MAX_ATTEMPTS:
                # Small vocabularies (e.g. the word fallback) can run out
                synthetic_value = f"{synthetic_value}-{attempt}"
        
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
        attempt: int = 0,
    ) -> str:
        """
        Generate synthetic data for a specific entity type.
        
        Args:
            entity_type: Type of PII entity
            original_value: Original value (for format preservation)
            entity_index: Entity index (unused; kept for subclasses)
            attempt: Retry counter used to resolve collisions
        
        Returns:
            Synthetic value
        """
        # Keyed, deterministic seed derived from the original value
        digest = hmac.new(
            self._seed_key,
            f"{attempt}:{original_value}".encode("utf-8"),
            hashlib.sha256,
        ).digest()
        self.fake.seed_instance(int.from_bytes(digest[:8], "big"))
        
        # Generate based on entity type
        if entity_type in ("PERSON", "NAME"):
            return str(self.fake.name())
        
        elif entity_type == "EMAIL":
            return str(self.fake.email())
        
        elif entity_type in ("PHONE", "PHONE_NUMBER"):
            # Try to preserve format
            if "-" in original_value:
                return str(self.fake.phone_number())
            else:
                return str(self.fake.phone_number().replace("-", ""))
        
        elif entity_type == "SSN":
            return str(self.fake.ssn())
        
        elif entity_type == "CREDIT_CARD":
            return str(self.fake.credit_card_number())
        
        elif entity_type in ("ADDRESS", "LOCATION"):
            return str(self.fake.address().replace("\n", ", "))
        
        elif entity_type == "CITY":
            return str(self.fake.city())
        
        elif entity_type == "STATE":
            return str(self.fake.state())
        
        elif entity_type == "COUNTRY":
            return str(self.fake.country())
        
        elif entity_type == "ZIP_CODE":
            return str(self.fake.zipcode())
        
        elif entity_type == "COMPANY":
            return str(self.fake.company())
        
        elif entity_type == "IP_ADDRESS":
            if ":" in original_value:  # IPv6
                return str(self.fake.ipv6())
            else:  # IPv4
                return str(self.fake.ipv4())
        
        elif entity_type == "URL":
            return str(self.fake.url())
        
        elif entity_type == "USERNAME":
            return str(self.fake.user_name())
        
        elif entity_type == "DATE":
            return str(self.fake.date())
        
        elif entity_type == "TIME":
            return str(self.fake.time())
        
        else:
            # Fallback: generate a word
            return str(self.fake.word())
    
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


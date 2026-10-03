"""
Hash-based anonymization for analytics use cases.
"""

import hmac
import secrets
from typing import Dict, Optional
from .base import BaseAnonymizer


class HashAnonymizer(BaseAnonymizer):
    """
    Anonymizer that replaces PII with keyed hashes (HMAC).
    
    Features:
    - Preserves uniqueness (same input and key → same hash)
    - Suitable for analytics and aggregation
    - One-way: values are hashed with HMAC under a secret key, so a hash
      cannot be reversed by hashing candidate values without the key.
      A plain or publicly salted hash of low-entropy PII (phone numbers,
      SSNs, dates of birth) can be reversed by hashing every possible value.
    - SHA-256 or SHA-512

    Pass the same ``salt`` to get the same hashes in different processes.
    Without it, each instance uses a random key, so hashes are only
    comparable within that instance.
    """
    
    def __init__(
        self,
        algorithm: str = "sha256",
        salt: Optional[str] = None,
        truncate: Optional[int] = None,
    ):
        """
        Initialize hash anonymizer.
        
        Args:
            algorithm: Hash algorithm ("sha256" or "sha512")
            salt: Secret used as the HMAC key. Treat it like a password: anyone
                who has it can confirm guesses of the original values. If
                omitted or empty, a random 256-bit key is generated.
            truncate: Optional number of characters to keep from hash
        """
        self.algorithm = algorithm.lower()
        self.salt = salt or ""
        self.truncate = truncate
        
        if self.algorithm not in ("sha256", "sha512"):
            raise ValueError(
                f"Unsupported algorithm: {algorithm}. "
                "Supported: sha256, sha512"
            )

        self._key = self.salt.encode("utf-8") if self.salt else secrets.token_bytes(32)
        
        self._mapping: Dict[str, str] = {}
        self._hashed_to_original: Dict[str, str] = {}
    
    def anonymize_entity(
        self,
        entity_type: str,
        original_value: str,
        entity_index: int,
    ) -> str:
        """
        Replace entity with its keyed hash.
        
        Args:
            entity_type: Type of PII entity
            original_value: Original PII value
            entity_index: Index of this entity type
        
        Returns:
            Hashed value
        """
        hashed = hmac.new(
            self._key, original_value.encode("utf-8"), self.algorithm
        ).hexdigest()
        
        # Truncate if requested
        if self.truncate:
            hashed = hashed[:self.truncate]
        
        # Store mapping (for informational purposes, cannot reverse)
        self._hashed_to_original[hashed] = original_value
        self._mapping[hashed] = original_value
        
        return hashed
    
    def get_mapping(self) -> Dict[str, str]:
        """
        Get mapping from hashed to original values.
        
        Note: This is stored for auditing but hashing is one-way.
        """
        return self._mapping.copy()
    
    def reset(self):
        """Reset all mappings."""
        self._mapping.clear()
        self._hashed_to_original.clear()


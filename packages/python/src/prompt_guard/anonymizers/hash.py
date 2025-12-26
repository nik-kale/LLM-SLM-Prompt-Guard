"""
Hash-based anonymization for analytics use cases.
"""

import hashlib
from typing import Dict, Optional
from .base import BaseAnonymizer


class HashAnonymizer(BaseAnonymizer):
    """
    Anonymizer that replaces PII with cryptographic hashes.
    
    Features:
    - Preserves uniqueness (same input → same hash)
    - Suitable for analytics and aggregation
    - One-way transformation (cannot reverse without rainbow tables)
    - Optional salt for additional security
    - Multiple hash algorithms (SHA256, SHA512, MD5)
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
            algorithm: Hash algorithm ("sha256", "sha512", "md5")
            salt: Optional salt to add to values before hashing
            truncate: Optional number of characters to keep from hash
        """
        self.algorithm = algorithm.lower()
        self.salt = salt or ""
        self.truncate = truncate
        
        if self.algorithm not in ("sha256", "sha512", "md5"):
            raise ValueError(
                f"Unsupported algorithm: {algorithm}. "
                "Supported: sha256, sha512, md5"
            )
        
        self._mapping: Dict[str, str] = {}
        self._hashed_to_original: Dict[str, str] = {}
    
    def anonymize_entity(
        self,
        entity_type: str,
        original_value: str,
        entity_index: int,
    ) -> str:
        """
        Replace entity with its hash.
        
        Args:
            entity_type: Type of PII entity
            original_value: Original PII value
            entity_index: Index of this entity type
        
        Returns:
            Hashed value
        """
        # Compute hash
        salted_value = f"{self.salt}{original_value}".encode('utf-8')
        
        if self.algorithm == "sha256":
            hash_obj = hashlib.sha256(salted_value)
        elif self.algorithm == "sha512":
            hash_obj = hashlib.sha512(salted_value)
        else:  # md5
            hash_obj = hashlib.md5(salted_value)
        
        hashed = hash_obj.hexdigest()
        
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


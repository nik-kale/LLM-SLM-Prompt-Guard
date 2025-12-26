"""
Encryption-based anonymization for reversible protection.
"""

import base64
from typing import Dict, Optional
from .base import BaseAnonymizer

try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class EncryptAnonymizer(BaseAnonymizer):
    """
    Anonymizer that encrypts PII values using Fernet (AES).
    
    Features:
    - Fully reversible with decryption key
    - AES encryption (GDPR Article 32 compliant)
    - Key management support
    - Suitable for secure storage
    
    Note: Keep the encryption key secure! Loss of key means data cannot be recovered.
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize encryption anonymizer.
        
        Args:
            encryption_key: Fernet encryption key (generates new if None)
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ImportError(
                "cryptography library is required for encryption anonymization. "
                "Install it with: pip install cryptography"
            )
        
        if encryption_key is None:
            # Generate new key
            self.key = Fernet.generate_key()
        else:
            self.key = encryption_key
        
        self.cipher = Fernet(self.key)
        self._mapping: Dict[str, str] = {}
    
    def anonymize_entity(
        self,
        entity_type: str,
        original_value: str,
        entity_index: int,
    ) -> str:
        """
        Encrypt the entity value.
        
        Args:
            entity_type: Type of PII entity
            original_value: Original PII value
            entity_index: Index of this entity type
        
        Returns:
            Encrypted value (base64 encoded)
        """
        # Encrypt
        encrypted_bytes = self.cipher.encrypt(original_value.encode('utf-8'))
        encrypted_str = base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        
        self._mapping[encrypted_str] = original_value
        return encrypted_str
    
    def deanonymize_value(self, encrypted_value: str) -> str:
        """
        Decrypt an encrypted value.
        
        Args:
            encrypted_value: Encrypted value to decrypt
        
        Returns:
            Original decrypted value
        """
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode('utf-8'))
        decrypted = self.cipher.decrypt(encrypted_bytes).decode('utf-8')
        return decrypted
    
    def get_mapping(self) -> Dict[str, str]:
        """Get mapping from encrypted to original values."""
        return self._mapping.copy()
    
    def get_encryption_key(self) -> bytes:
        """
        Get the encryption key.
        
        Returns:
            Encryption key (keep this secure!)
        """
        return self.key
    
    def reset(self):
        """Reset all mappings."""
        self._mapping.clear()


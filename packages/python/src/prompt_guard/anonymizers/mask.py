"""
Masking-based anonymization for partial redaction.
"""

from typing import Dict
from .base import BaseAnonymizer


class MaskAnonymizer(BaseAnonymizer):
    """
    Anonymizer that partially masks PII values.
    
    Features:
    - Configurable masking patterns
    - Partial reveal (e.g., show last 4 digits)
    - Format preservation
    - Useful for display purposes
    
    Examples:
    - Email: john@example.com → j***@e***.com
    - Phone: 555-123-4567 → ***-***-4567
    - Credit Card: 1234-5678-9012-3456 → ****-****-****-3456
    """
    
    def __init__(
        self,
        mask_char: str = "*",
        reveal_first: int = 0,
        reveal_last: int = 0,
        preserve_structure: bool = True,
    ):
        """
        Initialize mask anonymizer.
        
        Args:
            mask_char: Character to use for masking
            reveal_first: Number of characters to reveal at start
            reveal_last: Number of characters to reveal at end
            preserve_structure: Keep special characters like @, -, etc.
        """
        self.mask_char = mask_char
        self.reveal_first = reveal_first
        self.reveal_last = reveal_last
        self.preserve_structure = preserve_structure
        
        self._mapping: Dict[str, str] = {}
    
    def anonymize_entity(
        self,
        entity_type: str,
        original_value: str,
        entity_index: int,
    ) -> str:
        """
        Mask the entity value.
        
        Args:
            entity_type: Type of PII entity
            original_value: Original PII value
            entity_index: Index of this entity type
        
        Returns:
            Masked value
        """
        if self.preserve_structure:
            masked = self._mask_with_structure(original_value)
        else:
            masked = self._mask_simple(original_value)
        
        self._mapping[masked] = original_value
        return masked
    
    def _mask_simple(self, value: str) -> str:
        """Simple masking without structure preservation."""
        length = len(value)
        
        if length <= self.reveal_first + self.reveal_last:
            # If value is too short, just mask everything
            return self.mask_char * length
        
        start = value[:self.reveal_first] if self.reveal_first > 0 else ""
        end = value[-self.reveal_last:] if self.reveal_last > 0 else ""
        middle_len = length - self.reveal_first - self.reveal_last
        middle = self.mask_char * middle_len
        
        return start + middle + end
    
    def _mask_with_structure(self, value: str) -> str:
        """Mask while preserving special characters."""
        # Characters to preserve
        preserve_chars = set("@.-_:/() ")
        
        result = []
        char_count = 0
        
        for char in value:
            if char in preserve_chars:
                # Keep special characters
                result.append(char)
            else:
                # Determine if this character should be revealed or masked
                total_chars = sum(1 for c in value if c not in preserve_chars)
                
                if char_count < self.reveal_first:
                    result.append(char)
                elif char_count >= total_chars - self.reveal_last:
                    result.append(char)
                else:
                    result.append(self.mask_char)
                
                char_count += 1
        
        return ''.join(result)
    
    def get_mapping(self) -> Dict[str, str]:
        """Get mapping from masked to original values."""
        return self._mapping.copy()
    
    def reset(self):
        """Reset all mappings."""
        self._mapping.clear()


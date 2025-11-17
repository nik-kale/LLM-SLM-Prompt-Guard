"""
Enhanced regex-based PII detector with international support.

This detector provides comprehensive pattern matching for:
- International phone numbers (E.164, country-specific formats)
- Email addresses (RFC 5322 compliant)
- Credit cards (Visa, MasterCard, Amex, Discover)
- Various ID formats (SSN, passport, tax IDs)
- IP addresses (IPv4 and IPv6)
- Names (multiple patterns)
- And more...
"""

import re
from typing import List, Dict, Pattern
from .base import BaseDetector
from ..types import DetectorResult

# Email (RFC 5322 compliant)
EMAIL_RE = re.compile(
    r"\b[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\b"
)

# International phone numbers
# E.164 format: +[country code][number]
PHONE_E164_RE = re.compile(r"\+[1-9]\d{1,14}\b")

# US/Canada phone numbers
PHONE_US_RE = re.compile(
    r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)

# UK phone numbers
PHONE_UK_RE = re.compile(
    r"(?:(?:\+44\s?|0)(?:\d{2}\s?\d{4}\s?\d{4}|\d{3}\s?\d{3}\s?\d{4}|\d{4}\s?\d{3}\s?\d{3}))"
)

# Generic international
PHONE_GENERIC_RE = re.compile(
    r"(?:\+?\d{1,4}[-.\s]?)?(?:\(?\d{1,4}\)?[-.\s]?)?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}"
)

# Names (multiple patterns)
# Simple capitalized names
NAME_SIMPLE_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")

# Names with titles
NAME_WITH_TITLE_RE = re.compile(
    r"\b(?:Mr\.?|Mrs\.?|Ms\.?|Miss|Dr\.?|Prof\.?|Sir|Madam)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"
)

# IP Addresses
# IPv4
IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)

# IPv6
IPV6_RE = re.compile(
    r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|"
    r"\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b|"
    r"\b::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}\b"
)

# Credit Cards
# Visa
CC_VISA_RE = re.compile(r"\b4\d{3}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")

# MasterCard
CC_MASTERCARD_RE = re.compile(r"\b5[1-5]\d{2}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")

# American Express
CC_AMEX_RE = re.compile(r"\b3[47]\d{2}[\s\-]?\d{6}[\s\-]?\d{5}\b")

# Discover
CC_DISCOVER_RE = re.compile(r"\b6(?:011|5\d{2})[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")

# Generic credit card (fallback)
CC_GENERIC_RE = re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")

# Social Security Numbers (US)
SSN_RE = re.compile(r"\b\d{3}[\s\-]?\d{2}[\s\-]?\d{4}\b")

# National Insurance Number (UK)
NIN_UK_RE = re.compile(r"\b[A-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b")

# Passport Numbers
# US Passport
PASSPORT_US_RE = re.compile(r"\b[A-Z]\d{8}\b|\b\d{9}\b")

# UK Passport
PASSPORT_UK_RE = re.compile(r"\b[0-9]{9}GBR[0-9]{7}[A-Z][0-9]{6}[A-Z]{3}[0-9]\b")

# Generic passport
PASSPORT_GENERIC_RE = re.compile(r"\b[A-Z]{1,2}\d{6,9}\b")

# Driver's License (US formats vary by state)
DRIVERS_LICENSE_US_RE = re.compile(r"\b[A-Z]{1,2}\d{5,8}\b")

# IBAN (International Bank Account Number)
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")

# Tax IDs
# US EIN
EIN_RE = re.compile(r"\b\d{2}[\s\-]?\d{7}\b")

# Dates of Birth
DOB_RE = re.compile(
    r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{2,4}[-/]\d{1,2}[-/]\d{1,2})\b"
)

# Medical Record Numbers (generic)
MRN_RE = re.compile(r"\bMRN[\s\-:]?\d{6,10}\b", re.IGNORECASE)

# URLs (for detecting potentially sensitive links)
URL_RE = re.compile(
    r"\b(?:https?://|www\.)[^\s/$.?#].[^\s]*\b"
)

# MAC Addresses
MAC_RE = re.compile(
    r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"
)

# Cryptocurrency Addresses
# Bitcoin
CRYPTO_BTC_RE = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")

# Ethereum
CRYPTO_ETH_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")


class EnhancedRegexDetector(BaseDetector):
    """
    Enhanced regex-based PII detector with international support.

    Detects:
    - EMAIL: Email addresses (RFC 5322 compliant)
    - PHONE: Phone numbers (US, UK, E.164, generic international)
    - PERSON: Person names (with and without titles)
    - IP_ADDRESS: IPv4 and IPv6 addresses
    - CREDIT_CARD: Credit card numbers (Visa, MC, Amex, Discover)
    - SSN: US Social Security Numbers
    - NIN_UK: UK National Insurance Numbers
    - PASSPORT: Passport numbers (US, UK, generic)
    - DRIVERS_LICENSE: US Driver's License numbers
    - IBAN: International Bank Account Numbers
    - EIN: US Employer Identification Numbers
    - DOB: Dates of Birth
    - MRN: Medical Record Numbers
    - URL: URLs
    - MAC_ADDRESS: MAC addresses
    - CRYPTO_ADDRESS: Cryptocurrency addresses (BTC, ETH)
    """

    def __init__(self, enable_all: bool = True, entity_types: List[str] = None):
        """
        Initialize enhanced regex detector.

        Args:
            enable_all: Enable all detectors by default
            entity_types: Specific entity types to detect (None = all)
        """
        self.enable_all = enable_all
        self.entity_types = set(entity_types) if entity_types else None

        # Define patterns with their entity types
        self.patterns: List[tuple[Pattern, str, int]] = [
            # Email (high priority)
            (EMAIL_RE, "EMAIL", 100),

            # Phone numbers (order matters - specific before generic)
            (PHONE_E164_RE, "PHONE", 90),
            (PHONE_US_RE, "PHONE", 85),
            (PHONE_UK_RE, "PHONE", 85),
            (PHONE_GENERIC_RE, "PHONE", 70),

            # Names
            (NAME_WITH_TITLE_RE, "PERSON", 95),
            (NAME_SIMPLE_RE, "PERSON", 80),

            # IP Addresses
            (IPV6_RE, "IP_ADDRESS", 100),
            (IPV4_RE, "IP_ADDRESS", 100),

            # Credit Cards (specific before generic)
            (CC_VISA_RE, "CREDIT_CARD", 95),
            (CC_MASTERCARD_RE, "CREDIT_CARD", 95),
            (CC_AMEX_RE, "CREDIT_CARD", 95),
            (CC_DISCOVER_RE, "CREDIT_CARD", 95),
            (CC_GENERIC_RE, "CREDIT_CARD", 70),

            # National IDs
            (SSN_RE, "SSN", 100),
            (NIN_UK_RE, "NIN_UK", 100),
            (EIN_RE, "EIN", 90),

            # Passports
            (PASSPORT_UK_RE, "PASSPORT", 100),
            (PASSPORT_US_RE, "PASSPORT", 90),
            (PASSPORT_GENERIC_RE, "PASSPORT", 70),

            # Other documents
            (DRIVERS_LICENSE_US_RE, "DRIVERS_LICENSE", 80),
            (IBAN_RE, "IBAN", 95),

            # Dates and medical
            (DOB_RE, "DOB", 70),
            (MRN_RE, "MRN", 95),

            # Technical
            (URL_RE, "URL", 100),
            (MAC_RE, "MAC_ADDRESS", 100),
            (CRYPTO_BTC_RE, "CRYPTO_ADDRESS", 95),
            (CRYPTO_ETH_RE, "CRYPTO_ADDRESS", 95),
        ]

    def _should_detect(self, entity_type: str) -> bool:
        """Check if this entity type should be detected."""
        if self.entity_types is None:
            return self.enable_all
        return entity_type in self.entity_types

    def detect(self, text: str) -> List[DetectorResult]:
        """
        Detect PII using enhanced regex patterns.

        Args:
            text: Text to analyze

        Returns:
            List of detected PII entities
        """
        results: List[DetectorResult] = []
        seen_spans = set()  # Track (start, end) to avoid duplicates

        # Sort patterns by priority (descending)
        sorted_patterns = sorted(self.patterns, key=lambda x: x[2], reverse=True)

        for pattern, entity_type, priority in sorted_patterns:
            if not self._should_detect(entity_type):
                continue

            for match in pattern.finditer(text):
                span = (match.start(), match.end())

                # Skip if this span overlaps with a higher-priority match
                overlaps = any(
                    start <= match.start() < end or start < match.end() <= end
                    for start, end in seen_spans
                )

                if not overlaps:
                    results.append(
                        DetectorResult(
                            entity_type=entity_type,
                            start=match.start(),
                            end=match.end(),
                            text=match.group(0),
                            confidence=priority / 100.0,  # Convert to 0-1 scale
                        )
                    )
                    seen_spans.add(span)

        return results


# Convenience function
def create_enhanced_detector(
    enable_all: bool = True,
    entity_types: List[str] = None
) -> EnhancedRegexDetector:
    """Create an enhanced regex detector instance."""
    return EnhancedRegexDetector(enable_all=enable_all, entity_types=entity_types)

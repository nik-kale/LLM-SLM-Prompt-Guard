import re
from typing import List
from .base import BaseDetector
from ..types import DetectorResult

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\-\s]{7,}\d")
# Simple name pattern - detects capitalized words that look like names
NAME_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")
# IP address pattern
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# Credit card pattern (simple)
CC_RE = re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")
# SSN pattern
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


class RegexDetector(BaseDetector):
    """
    Simple regex-based PII detector.

    Detects:
    - EMAIL: Email addresses
    - PHONE: Phone numbers
    - PERSON: Names (simple capitalized word patterns)
    - IP_ADDRESS: IPv4 addresses
    - CREDIT_CARD: Credit card numbers
    - SSN: Social Security Numbers
    """

    def detect(self, text: str) -> List[DetectorResult]:
        results: List[DetectorResult] = []

        # Detect emails
        for match in EMAIL_RE.finditer(text):
            results.append(
                DetectorResult(
                    entity_type="EMAIL",
                    start=match.start(),
                    end=match.end(),
                    text=match.group(0),
                )
            )

        # Detect phone numbers
        for match in PHONE_RE.finditer(text):
            results.append(
                DetectorResult(
                    entity_type="PHONE",
                    start=match.start(),
                    end=match.end(),
                    text=match.group(0),
                )
            )

        # Detect names
        for match in NAME_RE.finditer(text):
            results.append(
                DetectorResult(
                    entity_type="PERSON",
                    start=match.start(),
                    end=match.end(),
                    text=match.group(0),
                )
            )

        # Detect IP addresses
        for match in IP_RE.finditer(text):
            results.append(
                DetectorResult(
                    entity_type="IP_ADDRESS",
                    start=match.start(),
                    end=match.end(),
                    text=match.group(0),
                )
            )

        # Detect credit cards
        for match in CC_RE.finditer(text):
            results.append(
                DetectorResult(
                    entity_type="CREDIT_CARD",
                    start=match.start(),
                    end=match.end(),
                    text=match.group(0),
                )
            )

        # Detect SSNs
        for match in SSN_RE.finditer(text):
            results.append(
                DetectorResult(
                    entity_type="SSN",
                    start=match.start(),
                    end=match.end(),
                    text=match.group(0),
                )
            )

        return results

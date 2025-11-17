"""
Examples of creating custom PII detectors using the Prompt Guard Detector SDK.

This file demonstrates various approaches to building custom detectors:
1. Simple regex-based detector
2. Domain-specific detector (employee IDs, project codes, etc.)
3. Context-aware detector
4. ML-based detector template
5. Multi-pattern detector

Run this file to see the examples in action:
    python custom_detector_examples.py
"""

import re
from typing import List

from prompt_guard import PromptGuard
from prompt_guard.detectors.base import (
    BaseDetector,
    RegexBasedDetector,
    MLBasedDetector,
    detector_registry,
)
from prompt_guard.types import DetectorResult


# ============================================================================
# Example 1: Simple Custom Regex Detector
# ============================================================================


class EmployeeIDDetector(BaseDetector):
    """
    Detects employee IDs in the format EMP-XXXXXX.

    This is a simple example showing the minimal code needed
    for a custom detector.
    """

    def __init__(self):
        super().__init__(name="EmployeeIDDetector", version="1.0.0")
        self.pattern = re.compile(r"\bEMP-\d{6}\b")

    def detect(self, text: str) -> List[DetectorResult]:
        """Detect employee IDs in text."""
        results = []
        for match in self.pattern.finditer(text):
            results.append(
                DetectorResult(

                    entity_type="EMPLOYEE_ID",

                    start=match.start(),

                    end=match.end(),

                    text=match.group(),

                    confidence=1.0,
                

                )
            )
        return results


# ============================================================================
# Example 2: Using RegexBasedDetector Helper Class
# ============================================================================


class CorporateIDDetector(RegexBasedDetector):
    """
    Detects various corporate identifiers using the helper class.

    This shows how to use the RegexBasedDetector helper to easily
    add multiple patterns with validation.
    """

    def __init__(self):
        super().__init__(name="CorporateIDDetector", version="1.0.0")

        # Employee ID: EMP-XXXXXX
        self.add_pattern("EMPLOYEE_ID", r"\bEMP-\d{6}\b")

        # Project Code: PROJ-XXX
        self.add_pattern("PROJECT_CODE", r"\bPROJ-[A-Z]{3}\b")

        # Department Code: DEPT-XX
        self.add_pattern("DEPARTMENT_CODE", r"\bDEPT-\d{2}\b")

        # Badge Number: BADGE-XXXX with validation
        self.add_pattern(
            "BADGE_NUMBER",
            r"\bBADGE-\d{4}\b",
            validator=lambda x: int(x.split("-")[1]) < 9999,
        )

    def detect(self, text: str) -> List[DetectorResult]:
        """Detect all corporate identifiers."""
        return self.detect_patterns(text)


# ============================================================================
# Example 3: Context-Aware Detector
# ============================================================================


class MedicalRecordDetector(BaseDetector):
    """
    Detects medical record numbers with context awareness.

    This example shows how to use surrounding context to improve
    detection accuracy and reduce false positives.
    """

    def __init__(self):
        super().__init__(name="MedicalRecordDetector", version="1.0.0")
        # MRN pattern: MRN-XXXXXXXX
        self.mrn_pattern = re.compile(r"\b(?:MRN[-:]?\s*)?(\d{8})\b", re.IGNORECASE)
        # Context keywords that indicate medical records
        self.medical_context = [
            "patient",
            "medical record",
            "mrn",
            "chart",
            "hospital",
            "clinic",
        ]

    def detect(self, text: str) -> List[DetectorResult]:
        """Detect medical record numbers with context awareness."""
        results = []

        for match in self.mrn_pattern.finditer(text):
            # Extract surrounding context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].lower()

            # Check if medical context keywords are present
            has_medical_context = any(
                keyword in context for keyword in self.medical_context
            )

            # Adjust confidence score based on context
            score = 0.9 if has_medical_context else 0.5

            # Only include if score meets threshold
            if score >= 0.7:
                results.append(
                    DetectorResult(

                        entity_type="MEDICAL_RECORD_NUMBER",

                        start=match.start(),

                        end=match.end(),

                        text=match.group(),

                        confidence=score,
                    

                    )
                )

        return results


# ============================================================================
# Example 4: ML-Based Detector Template
# ============================================================================


class CustomMLDetector(MLBasedDetector):
    """
    Template for creating ML-based custom detectors.

    This shows the structure for integrating custom ML models.
    Replace the mock implementation with your actual model.
    """

    def __init__(self, threshold: float = 0.8):
        super().__init__(name="CustomMLDetector", version="1.0.0", threshold=threshold)
        # In a real implementation, you would load your model here
        # self.model = load_my_custom_model()

    def detect(self, text: str) -> List[DetectorResult]:
        """Detect PII using ML model."""
        results = []

        # Mock implementation - replace with actual model inference
        # In reality, you would:
        # 1. Tokenize the text
        # 2. Run through your model
        # 3. Extract entities and confidence scores

        # Example of how to use the helper method:
        # raw_results = self.model.predict(text)
        # filtered_results = self.filter_by_threshold(raw_results)

        return results

    def load_model(self, model_path: str) -> None:
        """Load custom ML model."""
        # Implement your model loading logic here
        # For example:
        # import pickle
        # with open(model_path, 'rb') as f:
        #     self.model = pickle.load(f)
        pass


# ============================================================================
# Example 5: Multi-Language Detector
# ============================================================================


class InternationalPhoneDetector(BaseDetector):
    """
    Detects phone numbers in multiple international formats.

    This example shows how to handle multiple patterns and
    international variations.
    """

    def __init__(self):
        super().__init__(name="InternationalPhoneDetector", version="1.0.0")
        self.supported_languages = ["en", "es", "fr", "de", "it"]

        # Compile patterns for different formats
        self.patterns = {
            "US": re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),
            "INTL_E164": re.compile(r"\+\d{1,3}\s?\d{1,14}\b"),
            "UK": re.compile(r"\b0\d{10}\b"),
            "GENERIC": re.compile(r"\b\d{10,15}\b"),
        }

    def detect(self, text: str) -> List[DetectorResult]:
        """Detect international phone numbers."""
        results = []
        seen_positions = set()

        for format_name, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                # Avoid duplicate detections at the same position
                pos = (match.start(), match.end())
                if pos in seen_positions:
                    continue

                seen_positions.add(pos)

                # Assign confidence based on format specificity
                score = 0.95 if format_name != "GENERIC" else 0.7

                results.append(
                    DetectorResult(

                        entity_type="PHONE_NUMBER",

                        start=match.start(),

                        end=match.end(),

                        text=match.group(),

                        confidence=score,
                    

                    )
                )

        return results


# ============================================================================
# Example 6: Composite Detector (Multiple Entity Types)
# ============================================================================


class FinancialDataDetector(RegexBasedDetector):
    """
    Detects various financial identifiers.

    This example shows a comprehensive detector for financial data
    including account numbers, routing numbers, SWIFT codes, etc.
    """

    def __init__(self):
        super().__init__(name="FinancialDataDetector", version="1.0.0")

        # Bank Account Number (8-17 digits)
        self.add_pattern(
            "BANK_ACCOUNT",
            r"\b\d{8,17}\b",
            validator=lambda x: len(x) >= 8,
        )

        # Routing Number (9 digits)
        self.add_pattern(
            "ROUTING_NUMBER",
            r"\b\d{9}\b",
            validator=self._validate_routing_number,
        )

        # SWIFT/BIC Code
        self.add_pattern(
            "SWIFT_CODE",
            r"\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b",
        )

        # IBAN (simplified)
        self.add_pattern(
            "IBAN",
            r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b",
        )

    def _validate_routing_number(self, number: str) -> bool:
        """
        Validate US routing number using checksum algorithm.

        This is a real validation algorithm used for routing numbers.
        """
        if len(number) != 9:
            return False

        # Checksum validation
        digits = [int(d) for d in number]
        checksum = (
            3 * (digits[0] + digits[3] + digits[6])
            + 7 * (digits[1] + digits[4] + digits[7])
            + (digits[2] + digits[5] + digits[8])
        ) % 10

        return checksum == 0

    def detect(self, text: str) -> List[DetectorResult]:
        """Detect financial identifiers."""
        return self.detect_patterns(text)


# ============================================================================
# Usage Examples and Tests
# ============================================================================


def run_examples():
    """Run all detector examples."""
    print("=" * 70)
    print("Custom Detector SDK Examples")
    print("=" * 70)

    # Example 1: Employee ID Detector
    print("\n1. Employee ID Detector")
    print("-" * 70)
    text1 = "Please contact EMP-123456 or EMP-789012 for assistance."
    detector1 = EmployeeIDDetector()
    guard1 = PromptGuard(policy="custom_enterprise", detectors=[detector1])
    anonymized1, mapping1 = guard1.anonymize(text1)
    print(f"Original:    {text1}")
    print(f"Anonymized:  {anonymized1}")
    print(f"Mapping:     {mapping1}")

    # Example 2: Corporate ID Detector
    print("\n2. Corporate ID Detector")
    print("-" * 70)
    text2 = "Project PROJ-ABC in DEPT-05 requires badge BADGE-1234."
    detector2 = CorporateIDDetector()
    guard2 = PromptGuard(policy="custom_enterprise", detectors=[detector2])
    anonymized2, mapping2 = guard2.anonymize(text2)
    print(f"Original:    {text2}")
    print(f"Anonymized:  {anonymized2}")
    print(f"Mapping:     {mapping2}")

    # Example 3: Medical Record Detector (with context)
    print("\n3. Medical Record Detector (Context-Aware)")
    print("-" * 70)
    text3a = "Patient's medical record number is 12345678"
    text3b = "The number 12345678 appears in the report"
    detector3 = MedicalRecordDetector()
    guard3 = PromptGuard(policy="custom_enterprise", detectors=[detector3])

    anonymized3a, mapping3a = guard3.anonymize(text3a)
    anonymized3b, mapping3b = guard3.anonymize(text3b)

    print(f"With context:    {text3a}")
    print(f"Anonymized:      {anonymized3a}")
    print(f"Detected:        {len(mapping3a) > 0}")

    print(f"\nWithout context: {text3b}")
    print(f"Anonymized:      {anonymized3b}")
    print(f"Detected:        {len(mapping3b) > 0}")

    # Example 4: International Phone Detector
    print("\n4. International Phone Detector")
    print("-" * 70)
    text4 = "Call +1-555-123-4567 or +44 20 7946 0958 for support."
    detector4 = InternationalPhoneDetector()
    guard4 = PromptGuard(policy="custom_enterprise", detectors=[detector4])
    anonymized4, mapping4 = guard4.anonymize(text4)
    print(f"Original:    {text4}")
    print(f"Anonymized:  {anonymized4}")
    print(f"Mapping:     {mapping4}")

    # Example 5: Financial Data Detector
    print("\n5. Financial Data Detector")
    print("-" * 70)
    text5 = "Transfer from account 123456789012 using SWIFT code ABCDEF12."
    detector5 = FinancialDataDetector()
    guard5 = PromptGuard(policy="custom_enterprise", detectors=[detector5])
    anonymized5, mapping5 = guard5.anonymize(text5)
    print(f"Original:    {text5}")
    print(f"Anonymized:  {anonymized5}")
    print(f"Mapping:     {mapping5}")

    # Example 6: Using Detector Registry
    print("\n6. Using Detector Registry")
    print("-" * 70)
    detector_registry.register("employee_id", EmployeeIDDetector)
    detector_registry.register("corporate", CorporateIDDetector)

    print(f"Registered detectors: {detector_registry.list_detectors()}")

    emp_detector = detector_registry.create("employee_id")
    print(f"Created detector: {emp_detector.name}")

    # Example 7: Combining Multiple Custom Detectors
    print("\n7. Combining Multiple Custom Detectors")
    print("-" * 70)
    text7 = "EMP-123456 from DEPT-05 called +1-555-123-4567 about PROJ-ABC."
    guard7 = PromptGuard(
        detectors=[
            EmployeeIDDetector(),
            CorporateIDDetector(),
            InternationalPhoneDetector(),
        ]
    )
    anonymized7, mapping7 = guard7.anonymize(text7)
    print(f"Original:    {text7}")
    print(f"Anonymized:  {anonymized7}")
    print(f"Entities detected: {len(mapping7)}")
    print(f"Mapping:     {mapping7}")

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    run_examples()

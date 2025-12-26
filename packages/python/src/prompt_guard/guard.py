from __future__ import annotations

from typing import List, Dict, Tuple, Any, Optional
import yaml
import pathlib

from .detectors.regex_detector import RegexDetector
from .types import DetectorResult, Mapping, AnonymizeResult, AnonymizeOptions


class PromptGuard:
    """
    Core class for PII anonymization & de-anonymization.

    Example:
        >>> guard = PromptGuard(detectors=["regex"], policy="default_pii")
        >>> text = "Hi, I'm John Smith. My email is john@example.com."
        >>> anonymized, mapping = guard.anonymize(text)
        >>> print(anonymized)
        "Hi, I'm [NAME_1]. My email is [EMAIL_1]."
        >>> # After getting LLM/SLM response...
        >>> final = guard.deanonymize(llm_response, mapping)
    """

    def __init__(
        self,
        detectors: List[str] | None = None,
        policy: str = "default_pii",
        custom_policy_path: str | None = None,
    ):
        """
        Initialize PromptGuard.

        Args:
            detectors: List of detector backend names. Currently supports: ["regex"]
            policy: Name of built-in policy to use (e.g., "default_pii")
            custom_policy_path: Path to a custom policy YAML file
        """
        self.detectors = self._init_detectors(detectors or ["regex"])
        self.policy = self._load_policy(policy, custom_policy_path)

    def _init_detectors(self, names: List[str]):
        """Initialize detector backends."""
        instances = []
        for name in names:
            if name == "regex":
                instances.append(RegexDetector())
            elif name == "presidio":
                try:
                    from .detectors.presidio_detector import PresidioDetector
                    instances.append(PresidioDetector())
                except ImportError:
                    raise ValueError(
                        "Presidio detector is not available. "
                        "Install it with: pip install presidio-analyzer"
                    )
            else:
                raise ValueError(
                    f"Unknown detector backend: {name}. "
                    f"Currently supported: ['regex', 'presidio']"
                )
        return instances

    def _load_policy(
        self, policy_name: str, custom_path: str | None = None
    ) -> Dict[str, Any]:
        """Load policy configuration from YAML file."""
        if custom_path:
            policy_path = pathlib.Path(custom_path)
        else:
            policy_path = (
                pathlib.Path(__file__).parent / "policies" / f"{policy_name}.yaml"
            )

        if not policy_path.exists():
            raise FileNotFoundError(f"Policy file not found: {policy_path}")

        with policy_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def anonymize(
        self,
        text: str,
        options: Optional[AnonymizeOptions] = None,
        min_confidence: Optional[float] = None,
    ) -> AnonymizeResult:
        """
        Anonymize PII in the given text.

        Args:
            text: The text to anonymize
            options: Anonymization options (takes precedence over min_confidence)
            min_confidence: Minimum confidence threshold for ML detectors (0.0-1.0)
                          Shorthand for options.min_confidence

        Returns:
            A tuple of (anonymized_text, mapping) where mapping is a dict
            of placeholder -> original value
        """
        # Handle options
        if options is None:
            options = AnonymizeOptions()
            if min_confidence is not None:
                options.min_confidence = min_confidence

        all_results: List[DetectorResult] = []
        for detector in self.detectors:
            all_results.extend(detector.detect(text))

        # Filter by confidence if needed
        if options.min_confidence > 0:
            all_results = [
                r for r in all_results
                if r.confidence is None or r.confidence >= options.min_confidence
            ]

        # Sort by start index so replacements are stable
        all_results.sort(key=lambda r: r.start)

        policy_entities = self.policy.get("entities", {})
        mapping: Mapping = {}
        anonymized = []
        last_idx = 0

        # Counter per entity type
        counters: Dict[str, int] = {}

        for res in all_results:
            entity_cfg = policy_entities.get(res.entity_type)
            if not entity_cfg:
                continue  # skip unconfigured entity types

            # Add text before this entity
            anonymized.append(text[last_idx : res.start])

            # Compute placeholder
            counters[res.entity_type] = counters.get(res.entity_type, 0) + 1
            i = counters[res.entity_type]
            placeholder_tpl = entity_cfg.get(
                "placeholder", f"[{res.entity_type}_{{i}}]"
            )
            placeholder = placeholder_tpl.format(i=i)

            anonymized.append(placeholder)
            mapping[placeholder] = res.text

            last_idx = res.end

        # Add trailing text
        anonymized.append(text[last_idx:])

        return "".join(anonymized), mapping

    def deanonymize(self, text: str, mapping: Mapping) -> str:
        """
        Replace placeholders in text with original values from mapping.

        Args:
            text: Text containing placeholders
            mapping: Dictionary mapping placeholders to original values

        Returns:
            Text with placeholders replaced by original values
        """
        result = text
        for placeholder, original in mapping.items():
            result = result.replace(placeholder, original)
        return result

    def batch_anonymize(
        self,
        texts: List[str],
        options: Optional[AnonymizeOptions] = None,
        min_confidence: Optional[float] = None,
    ) -> List[AnonymizeResult]:
        """
        Anonymize multiple texts in batch.

        Args:
            texts: List of texts to anonymize
            options: Anonymization options (takes precedence over min_confidence)
            min_confidence: Minimum confidence threshold for ML detectors (0.0-1.0)

        Returns:
            List of (anonymized_text, mapping) tuples
        """
        return [
            self.anonymize(text, options=options, min_confidence=min_confidence)
            for text in texts
        ]

    def batch_deanonymize(
        self, texts: List[str], mappings: List[Mapping]
    ) -> List[str]:
        """
        De-anonymize multiple texts in batch.

        Args:
            texts: List of texts containing placeholders
            mappings: List of mappings corresponding to each text

        Returns:
            List of de-anonymized texts
        """
        if len(texts) != len(mappings):
            raise ValueError("Number of texts and mappings must match")

        return [
            self.deanonymize(text, mapping)
            for text, mapping in zip(texts, mappings)
        ]

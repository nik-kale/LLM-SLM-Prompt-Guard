from __future__ import annotations

from typing import List, Dict, Tuple, Any, Union
import yaml
import pathlib

from .detectors.regex_detector import RegexDetector
from .detectors.base import BaseDetector
from .types import DetectorResult, Mapping, AnonymizeResult


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
        detectors: List[Union[str, BaseDetector]] | None = None,
        policy: str = "default_pii",
        custom_policy_path: str | None = None,
    ):
        """
        Initialize PromptGuard.

        Args:
            detectors: List of detector backend names or detector instances.
                      String names: ["regex", "presidio", "spacy", "enhanced_regex"]
                      Or pass custom detector instances: [MyCustomDetector()]
            policy: Name of built-in policy to use (e.g., "default_pii")
            custom_policy_path: Path to a custom policy YAML file

        Example:
            >>> # Using built-in detectors
            >>> guard = PromptGuard(detectors=["regex"])
            >>>
            >>> # Using custom detector instances
            >>> from my_detectors import CustomDetector
            >>> guard = PromptGuard(detectors=[CustomDetector()])
            >>>
            >>> # Mixing built-in and custom
            >>> guard = PromptGuard(detectors=["regex", CustomDetector()])
        """
        self.detectors = self._init_detectors(detectors or ["regex"])
        self.policy = self._load_policy(policy, custom_policy_path)

    def _init_detectors(self, detectors: List[Union[str, BaseDetector]]):
        """
        Initialize detector backends.

        Args:
            detectors: List of detector names (strings) or detector instances

        Returns:
            List of detector instances
        """
        instances = []
        for item in detectors:
            # Check if it's already a detector instance
            if isinstance(item, BaseDetector):
                instances.append(item)
                continue

            # Otherwise, treat it as a string name
            name = item
            if name == "regex":
                instances.append(RegexDetector())
            elif name == "presidio":
                try:
                    from .detectors.presidio_detector import PresidioDetector
                    instances.append(PresidioDetector())
                except ImportError as e:
                    raise ValueError(
                        f"Presidio detector is not available.\n\n"
                        f"To use Presidio for ML-based PII detection, install it with:\n"
                        f"  pip install llm-slm-prompt-guard[presidio]\n\n"
                        f"Or install presidio-analyzer and spacy separately:\n"
                        f"  pip install presidio-analyzer spacy\n"
                        f"  python -m spacy download en_core_web_lg\n\n"
                        f"Original error: {str(e)}"
                    ) from e
            elif name == "enhanced_regex":
                try:
                    from .detectors.enhanced_regex_detector import EnhancedRegexDetector
                    instances.append(EnhancedRegexDetector())
                except ImportError as e:
                    raise ValueError(
                        f"Enhanced regex detector is not available.\n\n"
                        f"Install it with:\n"
                        f"  pip install llm-slm-prompt-guard\n\n"
                        f"Original error: {str(e)}"
                    ) from e
            elif name == "spacy":
                try:
                    from .detectors.spacy_detector import SpacyDetector
                    instances.append(SpacyDetector())
                except ImportError as e:
                    raise ValueError(
                        f"spaCy detector is not available.\n\n"
                        f"To use spaCy for NER-based PII detection, install it with:\n"
                        f"  pip install llm-slm-prompt-guard[spacy]\n\n"
                        f"Or install spacy separately:\n"
                        f"  pip install spacy\n"
                        f"  python -m spacy download en_core_web_sm\n\n"
                        f"Original error: {str(e)}"
                    ) from e
            else:
                available_detectors = ["regex", "enhanced_regex", "presidio", "spacy"]
                raise ValueError(
                    f"Unknown detector backend: '{name}'.\n\n"
                    f"Available detectors: {', '.join(available_detectors)}\n\n"
                    f"Example usage:\n"
                    f"  guard = PromptGuard(detectors=['regex'])\n"
                    f"  guard = PromptGuard(detectors=['presidio'])  # requires: pip install llm-slm-prompt-guard[presidio]\n\n"
                    f"For more information, see: https://github.com/nik-kale/llm-slm-prompt-guard"
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
            from . import list_policies
            available = list_policies()
            raise FileNotFoundError(
                f"Policy file not found: {policy_path}\n\n"
                f"Available built-in policies: {', '.join(available)}\n\n"
                f"Example usage:\n"
                f"  guard = PromptGuard(policy='default_pii')\n"
                f"  guard = PromptGuard(policy='hipaa_phi')\n"
                f"  guard = PromptGuard(custom_policy_path='/path/to/custom.yaml')\n\n"
                f"To create a custom policy, see: docs/policies.md"
            )

        try:
            with policy_path.open("r", encoding="utf-8") as f:
                policy_data = yaml.safe_load(f)

            # Validate policy structure
            if not isinstance(policy_data, dict):
                raise ValueError(
                    f"Invalid policy format in {policy_path}: Policy must be a YAML dictionary.\n\n"
                    f"Expected format:\n"
                    f"  entities:\n"
                    f"    - type: EMAIL\n"
                    f"      action: anonymize\n"
                )

            if "entities" not in policy_data:
                raise ValueError(
                    f"Invalid policy format in {policy_path}: Missing 'entities' key.\n\n"
                    f"Expected format:\n"
                    f"  entities:\n"
                    f"    - type: EMAIL\n"
                    f"      action: anonymize\n"
                )

            return policy_data
        except yaml.YAMLError as e:
            raise ValueError(
                f"Failed to parse policy file {policy_path}.\n\n"
                f"YAML parsing error: {str(e)}\n\n"
                f"Please ensure your policy file is valid YAML format."
            ) from e

    def anonymize(self, text: str) -> AnonymizeResult:
        """
        Anonymize PII in the given text.

        Args:
            text: The text to anonymize

        Returns:
            A tuple of (anonymized_text, mapping) where mapping is a dict
            of placeholder -> original value
        """
        all_results: List[DetectorResult] = []
        for detector in self.detectors:
            all_results.extend(detector.detect(text))

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

    def batch_anonymize(self, texts: List[str]) -> List[AnonymizeResult]:
        """
        Anonymize multiple texts in batch.

        Args:
            texts: List of texts to anonymize

        Returns:
            List of (anonymized_text, mapping) tuples
        """
        return [self.anonymize(text) for text in texts]

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

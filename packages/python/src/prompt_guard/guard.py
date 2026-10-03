from __future__ import annotations

from typing import List, Dict, Tuple, Any, Optional, Callable
import yaml
import pathlib

from .detectors.regex_detector import RegexDetector
from .types import (
    DetectorResult,
    Mapping,
    AnonymizeResult,
    AnonymizeOptions,
    DetectionReport,
    OverlapStrategy,
)
from .report import generate_detection_report, HIGH_RISK_ENTITIES, MEDIUM_RISK_ENTITIES


def _risk_rank(entity_type: str) -> int:
    """Rank entity types by sensitivity, used to break ties between overlaps."""
    if entity_type in HIGH_RISK_ENTITIES:
        return 2
    if entity_type in MEDIUM_RISK_ENTITIES:
        return 1
    return 0


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
        overlap_strategy: OverlapStrategy = OverlapStrategy.LONGEST_MATCH,
    ):
        """
        Initialize PromptGuard.

        Args:
            detectors: List of detector backend names. Currently supports: ["regex"]
            policy: Name of built-in policy to use (e.g., "default_pii")
            custom_policy_path: Path to a custom policy YAML file
            overlap_strategy: Strategy for resolving overlapping entity detections
        """
        self.detectors = self._init_detectors(detectors or ["regex"])
        self.policy = self._load_policy(policy, custom_policy_path)
        self.overlap_strategy = overlap_strategy

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

    def _resolve_overlaps(
        self,
        results: List[DetectorResult],
        text: Optional[str] = None,
    ) -> List[DetectorResult]:
        """
        Resolve overlapping entity detections based on configured strategy.

        Overlapping detections are grouped into clusters. The strategy decides
        which detection in a cluster supplies the entity type and confidence,
        and the resolved entity spans the whole cluster, so no character that
        any detector flagged is left in the output.

        Args:
            results: List of detected entities (may contain overlaps)
            text: Original text, used to fill in the text of widened entities

        Returns:
            List of non-overlapping entities sorted by start position
        """
        if not results:
            return []

        indexed = list(enumerate(results))
        if self.overlap_strategy == OverlapStrategy.MERGE_SAME_TYPE:
            indexed = self._merge_same_type(indexed)

        rank = self._cluster_rank_key()
        indexed.sort(key=lambda item: (item[1].start, item[1].end))

        resolved: List[DetectorResult] = []
        cluster = [indexed[0]]
        cluster_end = indexed[0][1].end
        for item in indexed[1:]:
            if item[1].start < cluster_end:
                cluster.append(item)
                cluster_end = max(cluster_end, item[1].end)
            else:
                resolved.append(self._collapse_cluster(cluster, rank, text))
                cluster = [item]
                cluster_end = item[1].end
        resolved.append(self._collapse_cluster(cluster, rank, text))
        return resolved

    def _has_overlap(self, r1: DetectorResult, r2: DetectorResult) -> bool:
        """Check if two detection results overlap."""
        return not (r1.end <= r2.start or r2.end <= r1.start)

    def _cluster_rank_key(self) -> Callable[[Tuple[int, DetectorResult]], Tuple[float, ...]]:
        """
        Return the sort key that orders a cluster's detections best-first.

        Items are (detector order index, result) pairs. Ties on length are
        broken in favour of the higher-risk entity type, so an SSN that a
        broad phone pattern also matches is labelled as an SSN.
        """

        def length(r: DetectorResult) -> int:
            return r.end - r.start

        def confidence(r: DetectorResult) -> float:
            return r.confidence if r.confidence is not None else 1.0

        if self.overlap_strategy == OverlapStrategy.HIGHEST_CONFIDENCE:
            return lambda item: (
                -confidence(item[1]),
                -length(item[1]),
                -_risk_rank(item[1].entity_type),
                item[0],
            )
        if self.overlap_strategy == OverlapStrategy.FIRST_DETECTOR:
            return lambda item: (item[0],)
        # LONGEST_MATCH, and MERGE_SAME_TYPE for overlaps across types
        return lambda item: (-length(item[1]), -_risk_rank(item[1].entity_type), item[0])

    @staticmethod
    def _collapse_cluster(
        cluster: List[Tuple[int, DetectorResult]],
        rank: Callable[[Tuple[int, DetectorResult]], Tuple[float, ...]],
        text: Optional[str],
    ) -> DetectorResult:
        """Reduce a cluster of overlapping detections to one entity covering all of them."""
        winner = min(cluster, key=rank)[1]
        start = min(r.start for _, r in cluster)
        end = max(r.end for _, r in cluster)
        if start == winner.start and end == winner.end and (winner.text or text is None):
            return winner
        return DetectorResult(
            entity_type=winner.entity_type,
            start=start,
            end=end,
            text=text[start:end] if text is not None else winner.text,
            confidence=winner.confidence,
        )

    @staticmethod
    def _merge_same_type(
        indexed: List[Tuple[int, DetectorResult]],
    ) -> List[Tuple[int, DetectorResult]]:
        """Merge overlapping detections of the same entity type into single spans."""
        by_type: Dict[str, List[Tuple[int, DetectorResult]]] = {}
        for item in indexed:
            by_type.setdefault(item[1].entity_type, []).append(item)

        merged: List[Tuple[int, DetectorResult]] = []
        for entity_type, items in by_type.items():
            items.sort(key=lambda item: (item[1].start, item[1].end))
            groups: List[List[Tuple[int, DetectorResult]]] = []
            group_end = 0
            for item in items:
                if groups and item[1].start < group_end:
                    groups[-1].append(item)
                    group_end = max(group_end, item[1].end)
                else:
                    groups.append([item])
                    group_end = item[1].end

            for group in groups:
                if len(group) == 1:
                    merged.append(group[0])
                    continue
                scores = [r.confidence for _, r in group if r.confidence is not None]
                merged.append(
                    (
                        min(i for i, _ in group),
                        DetectorResult(
                            entity_type=entity_type,
                            start=min(r.start for _, r in group),
                            end=max(r.end for _, r in group),
                            text="",  # filled in from the source text when resolved
                            confidence=sum(scores) / len(scores) if scores else None,
                        ),
                    )
                )
        merged.sort(key=lambda item: item[0])
        return merged

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

        policy_entities = self.policy.get("entities", {})

        # Only entity types the policy redacts take part in overlap resolution.
        # Otherwise an unconfigured type (e.g. a PHONE match over an SSN under a
        # policy without PHONE) could win the overlap and then be skipped,
        # leaving the configured entity in the output.
        all_results = [r for r in all_results if policy_entities.get(r.entity_type)]

        # Resolve overlapping entities (result is sorted by start index)
        all_results = self._resolve_overlaps(all_results, text)

        mapping: Mapping = {}
        anonymized = []
        last_idx = 0

        # Counter per entity type
        counters: Dict[str, int] = {}

        for res in all_results:
            entity_cfg = policy_entities[res.entity_type]

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
            mapping[placeholder] = text[res.start : res.end]

            last_idx = res.end

        # Add trailing text
        anonymized.append(text[last_idx:])

        return "".join(anonymized), mapping

    def detect_only(
        self,
        text: str,
        min_confidence: Optional[float] = None,
        include_preview: bool = False,
    ) -> DetectionReport:
        """
        Detect PII entities without performing anonymization (dry-run mode).
        
        Useful for:
        - Compliance auditing and reporting
        - Debugging detector configurations
        - Generating PII statistics
        - Tuning confidence thresholds
        
        Args:
            text: The text to analyze
            min_confidence: Minimum confidence threshold for ML detectors (0.0-1.0)
            include_preview: Include first 100 chars of text in report
        
        Returns:
            DetectionReport with statistics and risk assessment
        """
        all_results: List[DetectorResult] = []
        for detector in self.detectors:
            all_results.extend(detector.detect(text))
        
        # Filter by confidence if specified
        if min_confidence is not None and min_confidence > 0:
            all_results = [
                r for r in all_results
                if r.confidence is None or r.confidence >= min_confidence
            ]
        
        return generate_detection_report(text, all_results, include_preview)

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

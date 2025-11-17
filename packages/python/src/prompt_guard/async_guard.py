"""
Async version of PromptGuard with support for async/await patterns.

This module provides AsyncPromptGuard which supports:
- Async anonymization and de-anonymization
- Async batch processing
- Concurrent detector execution
- Async streaming support
"""

from __future__ import annotations

import asyncio
from typing import List, Dict, Tuple, Any, AsyncIterator, Optional
import pathlib
import yaml

from .detectors.regex_detector import RegexDetector
from .types import DetectorResult, Mapping, AnonymizeResult, AnonymizeOptions


class AsyncPromptGuard:
    """
    Async version of PromptGuard for async/await patterns.

    Example:
        >>> import asyncio
        >>> async def main():
        ...     guard = AsyncPromptGuard(policy="default_pii")
        ...     result = await guard.anonymize_async("Email: john@example.com")
        ...     print(result)
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        detectors: List[str] | None = None,
        policy: str = "default_pii",
        custom_policy_path: str | None = None,
        max_concurrent: int = 10,
    ):
        """
        Initialize AsyncPromptGuard.

        Args:
            detectors: List of detector backend names
            policy: Name of built-in policy to use
            custom_policy_path: Path to a custom policy YAML file
            max_concurrent: Maximum concurrent operations for batch processing
        """
        self.detectors = self._init_detectors(detectors or ["regex"])
        self.policy = self._load_policy(policy, custom_policy_path)
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

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

    async def anonymize_async(
        self,
        text: str,
        options: Optional[AnonymizeOptions] = None,
    ) -> AnonymizeResult:
        """
        Asynchronously anonymize PII in the given text.

        Args:
            text: The text to anonymize
            options: Anonymization options

        Returns:
            A tuple of (anonymized_text, mapping)
        """
        # Run detection in executor to avoid blocking
        loop = asyncio.get_event_loop()
        all_results = await loop.run_in_executor(
            None, self._run_detectors, text
        )

        # Process results (this is fast, so we can do it inline)
        return self._anonymize_with_results(text, all_results, options)

    def _run_detectors(self, text: str) -> List[DetectorResult]:
        """Run all detectors on the text."""
        all_results: List[DetectorResult] = []
        for detector in self.detectors:
            all_results.extend(detector.detect(text))
        return all_results

    def _anonymize_with_results(
        self,
        text: str,
        all_results: List[DetectorResult],
        options: Optional[AnonymizeOptions] = None,
    ) -> AnonymizeResult:
        """Anonymize text using detection results."""
        if options is None:
            options = AnonymizeOptions()

        # Filter by confidence if needed
        if options.min_confidence > 0:
            all_results = [
                r for r in all_results
                if r.confidence is None or r.confidence >= options.min_confidence
            ]

        # Sort by start index for stable replacements
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

    async def deanonymize_async(self, text: str, mapping: Mapping) -> str:
        """
        Asynchronously replace placeholders with original values.

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

    async def batch_anonymize(
        self,
        texts: List[str],
        options: Optional[AnonymizeOptions] = None,
    ) -> List[AnonymizeResult]:
        """
        Anonymize multiple texts concurrently.

        Args:
            texts: List of texts to anonymize
            options: Anonymization options

        Returns:
            List of (anonymized_text, mapping) tuples
        """
        async def _anonymize_one(text: str) -> AnonymizeResult:
            async with self._semaphore:
                return await self.anonymize_async(text, options)

        tasks = [_anonymize_one(text) for text in texts]
        return await asyncio.gather(*tasks)

    async def stream_anonymize(
        self,
        text_stream: AsyncIterator[str],
        options: Optional[AnonymizeOptions] = None,
    ) -> AsyncIterator[Tuple[str, Mapping]]:
        """
        Anonymize a stream of text chunks.

        Args:
            text_stream: Async iterator of text chunks
            options: Anonymization options

        Yields:
            Tuples of (anonymized_chunk, cumulative_mapping)
        """
        cumulative_mapping: Mapping = {}
        buffer = ""
        chunk_size = 100  # Process in chunks for efficiency

        async for chunk in text_stream:
            buffer += chunk

            # Process when buffer reaches chunk size
            if len(buffer) >= chunk_size:
                anonymized, new_mapping = await self.anonymize_async(
                    buffer, options
                )
                cumulative_mapping.update(new_mapping)
                yield anonymized, cumulative_mapping
                buffer = ""

        # Process remaining buffer
        if buffer:
            anonymized, new_mapping = await self.anonymize_async(buffer, options)
            cumulative_mapping.update(new_mapping)
            yield anonymized, cumulative_mapping


# Convenience factory function
def create_async_guard(
    detectors: List[str] | None = None,
    policy: str = "default_pii",
    **kwargs
) -> AsyncPromptGuard:
    """
    Create an AsyncPromptGuard instance.

    Args:
        detectors: List of detector backend names
        policy: Name of built-in policy to use
        **kwargs: Additional arguments for AsyncPromptGuard

    Returns:
        AsyncPromptGuard instance
    """
    return AsyncPromptGuard(detectors=detectors, policy=policy, **kwargs)

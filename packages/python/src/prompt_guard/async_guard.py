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
import re
from typing import List, Dict, Tuple, Any, AsyncIterator, Optional, Union

from .detectors.base import BaseDetector
from .guard import PromptGuard
from .types import (
    DetectorResult,
    Mapping,
    AnonymizeResult,
    AnonymizeOptions,
    DetectionReport,
    OverlapStrategy,
)
from .report import generate_detection_report

_WHITESPACE_RUN = re.compile(r"\s+")


class AsyncPromptGuard:
    """
    Async version of PromptGuard for async/await patterns.

    Detection runs in the default executor; overlap resolution, placeholder
    assignment and de-anonymization are shared with :class:`PromptGuard`.

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
        detectors: List[Union[str, BaseDetector]] | None = None,
        policy: str = "default_pii",
        custom_policy_path: str | None = None,
        max_concurrent: int = 10,
        overlap_strategy: OverlapStrategy = OverlapStrategy.LONGEST_MATCH,
    ):
        """
        Initialize AsyncPromptGuard.

        Args:
            detectors: Detector backend names and/or BaseDetector instances
            policy: Name of built-in policy to use
            custom_policy_path: Path to a custom policy YAML file
            max_concurrent: Maximum concurrent operations for batch processing
            overlap_strategy: Strategy for resolving overlapping entity detections
        """
        self._guard = PromptGuard(
            detectors=detectors,
            policy=policy,
            custom_policy_path=custom_policy_path,
            overlap_strategy=overlap_strategy,
        )
        self.max_concurrent = max_concurrent
        # Created on first use so it belongs to the running event loop.
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._semaphore_loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def detectors(self) -> List[Any]:
        return self._guard.detectors

    @detectors.setter
    def detectors(self, value: List[Any]) -> None:
        self._guard.detectors = value

    @property
    def policy(self) -> Dict[str, Any]:
        return self._guard.policy

    @policy.setter
    def policy(self, value: Dict[str, Any]) -> None:
        self._guard.policy = value

    def _get_semaphore(self) -> asyncio.Semaphore:
        loop = asyncio.get_running_loop()
        if self._semaphore is None or self._semaphore_loop is not loop:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
            self._semaphore_loop = loop
        return self._semaphore

    async def anonymize_async(
        self,
        text: str,
        options: Optional[AnonymizeOptions] = None,
        *,
        existing_mapping: Optional[Mapping] = None,
    ) -> AnonymizeResult:
        """
        Asynchronously anonymize PII in the given text.

        Args:
            text: The text to anonymize
            options: Anonymization options
            existing_mapping: Mapping to continue, see :meth:`PromptGuard.anonymize`

        Returns:
            A tuple of (anonymized_text, mapping)
        """
        all_results = await self._run_detectors_async(text)
        return self._anonymize_with_results(text, all_results, options, existing_mapping)

    async def _run_detectors_async(self, text: str) -> List[DetectorResult]:
        """Run detection in the default executor to avoid blocking the loop."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._run_detectors, text)

    def _run_detectors(self, text: str) -> List[DetectorResult]:
        """Run all detectors on the text."""
        return self._guard._detect(text)

    def _anonymize_with_results(
        self,
        text: str,
        all_results: List[DetectorResult],
        options: Optional[AnonymizeOptions] = None,
        existing_mapping: Optional[Mapping] = None,
    ) -> AnonymizeResult:
        """Anonymize text using detection results."""
        return self._guard._anonymize_with_results(
            text, all_results, options or AnonymizeOptions(), existing_mapping
        )

    async def detect_only_async(
        self,
        text: str,
        min_confidence: Optional[float] = None,
        include_preview: bool = False,
    ) -> DetectionReport:
        """
        Asynchronously detect PII entities without performing anonymization (dry-run mode).
        
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
        all_results = await self._run_detectors_async(text)
        
        # Filter by confidence if specified
        if min_confidence is not None and min_confidence > 0:
            all_results = [
                r for r in all_results
                if r.confidence is None or r.confidence >= min_confidence
            ]
        
        # Generate report in executor
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, generate_detection_report, text, all_results, include_preview
        )

    async def deanonymize_async(self, text: str, mapping: Mapping) -> str:
        """
        Asynchronously replace placeholders with original values.

        Args:
            text: Text containing placeholders
            mapping: Dictionary mapping placeholders to original values

        Returns:
            Text with placeholders replaced by original values
        """
        return self._guard.deanonymize(text, mapping)

    async def batch_anonymize(
        self,
        texts: List[str],
        options: Optional[AnonymizeOptions] = None,
    ) -> List[AnonymizeResult]:
        """
        Anonymize multiple texts concurrently.

        Each text gets its own mapping.

        Args:
            texts: List of texts to anonymize
            options: Anonymization options

        Returns:
            List of (anonymized_text, mapping) tuples
        """
        semaphore = self._get_semaphore()

        async def _anonymize_one(text: str) -> AnonymizeResult:
            async with semaphore:
                return await self.anonymize_async(text, options)

        tasks = [_anonymize_one(text) for text in texts]
        return await asyncio.gather(*tasks)

    async def stream_anonymize(
        self,
        text_stream: AsyncIterator[str],
        options: Optional[AnonymizeOptions] = None,
        chunk_size: int = 100,
        holdback: int = 64,
    ) -> AsyncIterator[Tuple[str, Mapping]]:
        """
        Anonymize a stream of text chunks.

        Incoming chunks are buffered and emitted in pieces of roughly
        ``chunk_size`` characters. A piece never ends inside a detected entity
        and always leaves the last ``holdback`` characters in the buffer, so
        PII that arrives split across chunks is still detected as a whole.
        All pieces share one mapping, so placeholders stay unique.

        Args:
            text_stream: Async iterator of text chunks
            options: Anonymization options
            chunk_size: Minimum number of characters to emit at a time
            holdback: Characters kept back as context for the next piece

        Yields:
            Tuples of (anonymized_piece, cumulative_mapping)
        """
        mapping: Mapping = {}
        buffer = ""

        async for chunk in text_stream:
            buffer += chunk
            if len(buffer) < chunk_size + holdback:
                continue

            results = await self._run_detectors_async(buffer)
            cut = self._safe_cut(buffer, results, len(buffer) - holdback)
            if cut <= 0:
                continue

            head = [r for r in results if r.end <= cut]
            anonymized, mapping = self._anonymize_with_results(
                buffer[:cut], head, options, mapping
            )
            yield anonymized, mapping
            buffer = buffer[cut:]

        # Process remaining buffer
        if buffer:
            anonymized, mapping = await self.anonymize_async(
                buffer, options, existing_mapping=mapping
            )
            yield anonymized, mapping

    @staticmethod
    def _safe_cut(text: str, results: List[DetectorResult], limit: int) -> int:
        """
        Return the largest position <= ``limit`` that is not inside a detected
        entity, preferring positions right after whitespace. Returns 0 if
        there is none.
        """
        spans = [(r.start, r.end) for r in results]

        def clear(position: int) -> bool:
            return not any(start < position < end for start, end in spans)

        for match in reversed(list(_WHITESPACE_RUN.finditer(text, 0, limit))):
            if clear(match.end()):
                return match.end()

        position = limit
        while position > 0 and not clear(position):
            position = min(start for start, end in spans if start < position < end)
        return position


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

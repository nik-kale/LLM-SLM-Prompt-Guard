"""
Tests for the OpenTelemetry decorators.
"""

import pytest

pytest.importorskip("opentelemetry.sdk")

from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (  # noqa: E402
    InMemorySpanExporter,
)

from prompt_guard.telemetry import Telemetry, TelemetryConfig  # noqa: E402


def test_failed_spans_do_not_export_exception_messages():
    # Exception messages (which can quote the PII being processed) used to be
    # exported as the span status and as an exception event.
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    telemetry = Telemetry(TelemetryConfig(enable_metrics=False))
    telemetry.tracer = provider.get_tracer("test")

    @telemetry.trace_anonymize
    def anonymize(text):
        raise ValueError(f"cannot handle {text!r}")

    with pytest.raises(ValueError):
        anonymize("SSN 123-45-6789")

    (span,) = exporter.get_finished_spans()
    exported = repr(span.to_json())
    assert "123-45-6789" not in exported
    assert span.status.description == "ValueError"
    assert span.attributes["exception.type"] == "ValueError"

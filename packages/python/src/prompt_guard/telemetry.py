"""
OpenTelemetry integration for distributed tracing and metrics.
"""

from typing import List, Optional, Dict, Any
from functools import wraps
import time

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.metrics import Counter, Histogram
    
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    # Provide no-op implementations
    trace = None
    metrics = None


class TelemetryConfig:
    """Configuration for OpenTelemetry telemetry."""
    
    def __init__(
        self,
        service_name: str = "prompt-guard",
        enable_tracing: bool = True,
        enable_metrics: bool = True,
        export_to_console: bool = False,
    ):
        """
        Initialize telemetry configuration.
        
        Args:
            service_name: Service name for telemetry
            enable_tracing: Enable distributed tracing
            enable_metrics: Enable metrics collection
            export_to_console: Export to console (useful for debugging)
        """
        self.service_name = service_name
        self.enable_tracing = enable_tracing
        self.enable_metrics = enable_metrics
        self.export_to_console = export_to_console


class Telemetry:
    """
    OpenTelemetry integration for Prompt Guard.
    
    Provides:
    - Distributed tracing for anonymization operations
    - Metrics for detection counts and latency
    - Automatic span attributes for entity types and counts
    """
    
    def __init__(self, config: Optional[TelemetryConfig] = None):
        """
        Initialize telemetry.
        
        Args:
            config: Telemetry configuration
        """
        self.config = config or TelemetryConfig()
        self.enabled = OTEL_AVAILABLE
        self.tracer = None
        self.meter = None
        
        # Metrics
        self.anonymize_counter: Optional[Counter] = None
        self.deanonymize_counter: Optional[Counter] = None
        self.detection_counter: Optional[Counter] = None
        self.latency_histogram: Optional[Histogram] = None
        
        if self.enabled:
            self._setup()
    
    def _setup(self):
        """Setup OpenTelemetry providers and exporters."""
        if not OTEL_AVAILABLE:
            return
        
        # Setup tracing
        if self.config.enable_tracing:
            tracer_provider = TracerProvider()
            
            if self.config.export_to_console:
                span_processor = BatchSpanProcessor(ConsoleSpanExporter())
                tracer_provider.add_span_processor(span_processor)
            
            trace.set_tracer_provider(tracer_provider)
            self.tracer = trace.get_tracer(self.config.service_name)
        
        # Setup metrics
        if self.config.enable_metrics:
            if self.config.export_to_console:
                metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
                meter_provider = MeterProvider(metric_readers=[metric_reader])
            else:
                meter_provider = MeterProvider()
            
            metrics.set_meter_provider(meter_provider)
            self.meter = metrics.get_meter(self.config.service_name)
            
            # Create metrics
            self.anonymize_counter = self.meter.create_counter(
                name="prompt_guard.anonymize.count",
                description="Number of anonymization operations",
                unit="1",
            )
            
            self.deanonymize_counter = self.meter.create_counter(
                name="prompt_guard.deanonymize.count",
                description="Number of de-anonymization operations",
                unit="1",
            )
            
            self.detection_counter = self.meter.create_counter(
                name="prompt_guard.detection.count",
                description="Number of PII entities detected",
                unit="1",
            )
            
            self.latency_histogram = self.meter.create_histogram(
                name="prompt_guard.operation.latency",
                description="Latency of operations in milliseconds",
                unit="ms",
            )
    
    def trace_anonymize(self, func):
        """
        Decorator to trace anonymization operations.
        
        Usage:
            @telemetry.trace_anonymize
            def anonymize(self, text):
                ...
        """
        if not self.enabled or not self.tracer:
            return func
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.tracer.start_as_current_span("anonymize") as span:
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Extract metadata from result
                    if isinstance(result, tuple) and len(result) == 2:
                        anonymized_text, mapping = result
                        entity_count = len(mapping)
                        
                        # Get entity types
                        entity_types = list(set([
                            k.split('_')[0].strip('[]') for k in mapping.keys()
                        ]))
                        
                        # Set span attributes
                        span.set_attribute("pii.entity_count", entity_count)
                        span.set_attribute("pii.entity_types", ",".join(entity_types))
                        span.set_attribute("pii.text_length", len(anonymized_text))
                        
                        # Record metrics
                        if self.anonymize_counter:
                            self.anonymize_counter.add(1)
                        if self.detection_counter:
                            self.detection_counter.add(
                                entity_count,
                                {"entity_types": ",".join(entity_types)}
                            )
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
                    
                finally:
                    # Record latency
                    latency_ms = (time.time() - start_time) * 1000
                    if self.latency_histogram:
                        self.latency_histogram.record(
                            latency_ms,
                            {"operation": "anonymize"}
                        )
        
        return wrapper
    
    def trace_deanonymize(self, func):
        """
        Decorator to trace de-anonymization operations.
        """
        if not self.enabled or not self.tracer:
            return func
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.tracer.start_as_current_span("deanonymize") as span:
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Record metrics
                    if self.deanonymize_counter:
                        self.deanonymize_counter.add(1)
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
                    
                finally:
                    # Record latency
                    latency_ms = (time.time() - start_time) * 1000
                    if self.latency_histogram:
                        self.latency_histogram.record(
                            latency_ms,
                            {"operation": "deanonymize"}
                        )
        
        return wrapper
    
    def trace_detection(self, detector_name: str):
        """
        Decorator to trace individual detector operations.
        
        Args:
            detector_name: Name of the detector
        """
        if not self.enabled or not self.tracer:
            return lambda func: func
        
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.tracer.start_as_current_span(f"detect.{detector_name}") as span:
                    start_time = time.time()
                    
                    try:
                        results = func(*args, **kwargs)
                        
                        # Set span attributes
                        span.set_attribute("detector.name", detector_name)
                        span.set_attribute("detector.result_count", len(results))
                        
                        span.set_status(Status(StatusCode.OK))
                        return results
                        
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
                        
                    finally:
                        # Record latency
                        latency_ms = (time.time() - start_time) * 1000
                        if self.latency_histogram:
                            self.latency_histogram.record(
                                latency_ms,
                                {"operation": f"detect.{detector_name}"}
                            )
            
            return wrapper
        
        return decorator


# Global telemetry instance
_global_telemetry: Optional[Telemetry] = None


def configure_telemetry(config: Optional[TelemetryConfig] = None) -> Telemetry:
    """
    Configure global telemetry instance.
    
    Args:
        config: Telemetry configuration
    
    Returns:
        Configured telemetry instance
    """
    global _global_telemetry
    _global_telemetry = Telemetry(config)
    return _global_telemetry


def get_telemetry() -> Optional[Telemetry]:
    """
    Get global telemetry instance.
    
    Returns:
        Telemetry instance or None if not configured
    """
    return _global_telemetry


def is_telemetry_available() -> bool:
    """
    Check if OpenTelemetry is available.
    
    Returns:
        True if OpenTelemetry packages are installed
    """
    return OTEL_AVAILABLE


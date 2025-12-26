"""
Event hook system for detection and anonymization lifecycle.
"""

from typing import List, Dict, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .types import DetectorResult, Mapping


class HookEvent(str, Enum):
    """Event types for hooks."""
    ON_DETECTION = "on_detection"  # Called for each detected entity
    PRE_ANONYMIZE = "pre_anonymize"  # Before anonymization
    POST_ANONYMIZE = "post_anonymize"  # After anonymization
    ON_ERROR = "on_error"  # On any error


@dataclass
class DetectionEvent:
    """Event data for entity detection."""
    entity: DetectorResult
    text: str
    detector_name: Optional[str] = None


@dataclass
class AnonymizeEvent:
    """Event data for anonymization."""
    original_text: str
    entities: List[DetectorResult]
    context: Dict[str, Any]


@dataclass
class AnonymizedEvent:
    """Event data after anonymization."""
    original_text: str
    anonymized_text: str
    mapping: Mapping
    entities: List[DetectorResult]
    context: Dict[str, Any]


@dataclass
class ErrorEvent:
    """Event data for errors."""
    error: Exception
    context: Dict[str, Any]


# Type aliases for hook functions
DetectionHook = Callable[[DetectionEvent], None]
PreAnonymizeHook = Callable[[AnonymizeEvent], Optional[AnonymizeEvent]]
PostAnonymizeHook = Callable[[AnonymizedEvent], Optional[AnonymizedEvent]]
ErrorHook = Callable[[ErrorEvent], None]


class HookRegistry:
    """
    Registry for managing event hooks.
    
    Allows registration of multiple hooks per event type and
    provides methods to trigger hooks during the detection/anonymization lifecycle.
    """
    
    def __init__(self):
        """Initialize empty hook registry."""
        self._hooks: Dict[HookEvent, List[Callable]] = {
            HookEvent.ON_DETECTION: [],
            HookEvent.PRE_ANONYMIZE: [],
            HookEvent.POST_ANONYMIZE: [],
            HookEvent.ON_ERROR: [],
        }
    
    def register(self, event: HookEvent, hook: Callable):
        """
        Register a hook for an event.
        
        Args:
            event: Event type to hook into
            hook: Callback function
        """
        if event not in self._hooks:
            raise ValueError(f"Unknown event type: {event}")
        
        self._hooks[event].append(hook)
    
    def unregister(self, event: HookEvent, hook: Callable):
        """
        Unregister a hook.
        
        Args:
            event: Event type
            hook: Callback function to remove
        """
        if event in self._hooks and hook in self._hooks[event]:
            self._hooks[event].remove(hook)
    
    def clear(self, event: Optional[HookEvent] = None):
        """
        Clear all hooks for an event (or all events if None).
        
        Args:
            event: Event type to clear (or None for all)
        """
        if event:
            self._hooks[event] = []
        else:
            for event_type in self._hooks:
                self._hooks[event_type] = []
    
    def trigger_detection(self, entity: DetectorResult, text: str, detector_name: Optional[str] = None):
        """
        Trigger ON_DETECTION hooks.
        
        Args:
            entity: Detected entity
            text: Original text
            detector_name: Name of detector that found the entity
        """
        event = DetectionEvent(entity=entity, text=text, detector_name=detector_name)
        
        for hook in self._hooks[HookEvent.ON_DETECTION]:
            try:
                hook(event)
            except Exception as e:
                # Don't let hook errors break the pipeline
                self._trigger_error(e, {"event": "on_detection", "entity": entity})
    
    def trigger_pre_anonymize(
        self,
        text: str,
        entities: List[DetectorResult],
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[AnonymizeEvent]:
        """
        Trigger PRE_ANONYMIZE hooks.
        
        Hooks can modify the event and return modified version.
        
        Args:
            text: Original text
            entities: Detected entities
            context: Additional context
        
        Returns:
            Modified event (or None if no modification)
        """
        event = AnonymizeEvent(
            original_text=text,
            entities=entities,
            context=context or {},
        )
        
        for hook in self._hooks[HookEvent.PRE_ANONYMIZE]:
            try:
                result = hook(event)
                if result is not None:
                    event = result
            except Exception as e:
                self._trigger_error(e, {"event": "pre_anonymize", "text_length": len(text)})
        
        return event
    
    def trigger_post_anonymize(
        self,
        original_text: str,
        anonymized_text: str,
        mapping: Mapping,
        entities: List[DetectorResult],
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[AnonymizedEvent]:
        """
        Trigger POST_ANONYMIZE hooks.
        
        Args:
            original_text: Original text
            anonymized_text: Anonymized text
            mapping: PII mapping
            entities: Detected entities
            context: Additional context
        
        Returns:
            Modified event (or None if no modification)
        """
        event = AnonymizedEvent(
            original_text=original_text,
            anonymized_text=anonymized_text,
            mapping=mapping,
            entities=entities,
            context=context or {},
        )
        
        for hook in self._hooks[HookEvent.POST_ANONYMIZE]:
            try:
                result = hook(event)
                if result is not None:
                    event = result
            except Exception as e:
                self._trigger_error(e, {"event": "post_anonymize", "entity_count": len(mapping)})
        
        return event
    
    def _trigger_error(self, error: Exception, context: Dict[str, Any]):
        """
        Trigger ON_ERROR hooks.
        
        Args:
            error: Exception that occurred
            context: Error context
        """
        event = ErrorEvent(error=error, context=context)
        
        for hook in self._hooks[HookEvent.ON_ERROR]:
            try:
                hook(event)
            except Exception:
                # Don't let error hook errors cause recursion
                pass
    
    def get_hook_count(self, event: HookEvent) -> int:
        """
        Get number of hooks registered for an event.
        
        Args:
            event: Event type
        
        Returns:
            Number of registered hooks
        """
        return len(self._hooks.get(event, []))


# Built-in hooks

class AlertHook:
    """
    Hook that sends alerts on high-risk entity detection.
    
    Useful for compliance teams to get notified when sensitive PII is detected.
    """
    
    def __init__(
        self,
        high_risk_entities: Optional[List[str]] = None,
        alert_callback: Optional[Callable] = None,
    ):
        """
        Initialize alert hook.
        
        Args:
            high_risk_entities: List of entity types to alert on
            alert_callback: Function to call when alert triggered
        """
        self.high_risk_entities = high_risk_entities or ["SSN", "CREDIT_CARD", "PASSPORT"]
        self.alert_callback = alert_callback or self._default_alert
    
    def __call__(self, event: DetectionEvent):
        """Hook callback for ON_DETECTION."""
        if event.entity.entity_type in self.high_risk_entities:
            self.alert_callback(event)
    
    def _default_alert(self, event: DetectionEvent):
        """Default alert handler (prints to console)."""
        print(f"⚠️  ALERT: High-risk PII detected - {event.entity.entity_type}")


class MetricsHook:
    """
    Hook that collects custom metrics.
    """
    
    def __init__(self):
        """Initialize metrics hook."""
        self.detection_counts: Dict[str, int] = {}
        self.total_detections = 0
        self.total_anonymizations = 0
    
    def on_detection(self, event: DetectionEvent):
        """Count detections by type."""
        entity_type = event.entity.entity_type
        self.detection_counts[entity_type] = self.detection_counts.get(entity_type, 0) + 1
        self.total_detections += 1
    
    def on_post_anonymize(self, event: AnonymizedEvent):
        """Count anonymizations."""
        self.total_anonymizations += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collected statistics."""
        return {
            "total_detections": self.total_detections,
            "total_anonymizations": self.total_anonymizations,
            "detection_counts": self.detection_counts.copy(),
        }
    
    def reset(self):
        """Reset all metrics."""
        self.detection_counts.clear()
        self.total_detections = 0
        self.total_anonymizations = 0


class AuditHook:
    """
    Hook that logs detailed audit information.
    """
    
    def __init__(self, audit_callback: Optional[Callable] = None):
        """
        Initialize audit hook.
        
        Args:
            audit_callback: Function to call for audit logging
        """
        self.audit_callback = audit_callback or self._default_audit
    
    def on_post_anonymize(self, event: AnonymizedEvent):
        """Log anonymization details."""
        audit_record = {
            "timestamp": None,  # Would be set by logging system
            "entity_count": len(event.mapping),
            "entity_types": list(set(e.entity_type for e in event.entities)),
            "text_length": len(event.original_text),
            "anonymized_length": len(event.anonymized_text),
        }
        self.audit_callback(audit_record)
    
    def _default_audit(self, record: Dict[str, Any]):
        """Default audit handler (prints to console)."""
        print(f"📋 AUDIT: Anonymized {record['entity_count']} entities: {record['entity_types']}")


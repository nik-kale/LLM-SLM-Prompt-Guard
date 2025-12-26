"""
Structured JSON logging for Prompt Guard with correlation IDs and context enrichment.
"""

import logging
import json
import uuid
import time
from typing import Dict, Any, Optional
from contextvars import ContextVar
from datetime import datetime


# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class JSONFormatter(logging.Formatter):
    """
    Structured JSON log formatter with automatic context enrichment.
    
    Outputs logs in JSON format with fields:
    - timestamp: ISO 8601 timestamp
    - level: Log level (INFO, ERROR, etc.)
    - logger: Logger name
    - message: Log message
    - request_id: Correlation ID for request tracing
    - session_id: PII session identifier
    - user_id: User identifier
    - context: Additional context fields
    - exception: Exception details if present
    """
    
    def __init__(self, include_extra: bool = True):
        """
        Initialize JSON formatter.
        
        Args:
            include_extra: Include extra fields from log record
        """
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
        
        Returns:
            JSON-formatted log string
        """
        # Base log structure
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add correlation IDs from context
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        session_id = session_id_var.get()
        if session_id:
            log_data["session_id"] = session_id
        
        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id
        
        # Add source location
        log_data["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }
        
        # Add extra fields (excluding standard fields)
        if self.include_extra:
            standard_fields = {
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info",
            }
            
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in standard_fields and not key.startswith("_"):
                    # Sanitize to prevent PII leakage
                    if not self._is_sensitive_field(key):
                        extra_fields[key] = value
            
            if extra_fields:
                log_data["context"] = extra_fields
        
        return json.dumps(log_data, default=str)
    
    @staticmethod
    def _is_sensitive_field(field_name: str) -> bool:
        """
        Check if a field name suggests sensitive data.
        
        Args:
            field_name: Field name to check
        
        Returns:
            True if field might contain sensitive data
        """
        sensitive_keywords = {
            "password", "secret", "token", "key", "ssn", "credit",
            "card", "email", "phone", "address", "pii", "personal",
        }
        field_lower = field_name.lower()
        return any(keyword in field_lower for keyword in sensitive_keywords)


class StructuredLogger:
    """
    Structured logger with context management and correlation tracking.
    """
    
    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        json_format: bool = True,
    ):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            level: Logging level
            json_format: Use JSON formatting
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []
        
        # Create handler
        handler = logging.StreamHandler()
        
        if json_format:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def set_request_id(self, request_id: Optional[str] = None) -> str:
        """
        Set request ID for correlation tracking.
        
        Args:
            request_id: Request ID (generates UUID if None)
        
        Returns:
            The request ID that was set
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        return request_id
    
    def set_session_id(self, session_id: str):
        """Set session ID in context."""
        session_id_var.set(session_id)
    
    def set_user_id(self, user_id: str):
        """Set user ID in context."""
        user_id_var.set(user_id)
    
    def clear_context(self):
        """Clear all context variables."""
        request_id_var.set(None)
        session_id_var.set(None)
        user_id_var.set(None)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message with context."""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self.logger.debug(message, extra=kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical message with context."""
        self.logger.critical(message, exc_info=exc_info, extra=kwargs)


def configure_logging(
    level: str = "INFO",
    json_format: bool = True,
    component_levels: Optional[Dict[str, str]] = None,
) -> None:
    """
    Configure logging for all Prompt Guard components.
    
    Args:
        level: Default log level
        json_format: Use JSON formatting
        component_levels: Per-component log levels
            e.g., {"prompt_guard.detectors": "DEBUG", "prompt_guard.storage": "WARNING"}
    """
    # Convert string level to int
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    root = logging.getLogger("prompt_guard")
    root.setLevel(numeric_level)
    root.handlers = []
    
    handler = logging.StreamHandler()
    
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    handler.setFormatter(formatter)
    root.addHandler(handler)
    
    # Configure component-specific levels
    if component_levels:
        for component, component_level in component_levels.items():
            component_logger = logging.getLogger(component)
            numeric_component_level = getattr(logging, component_level.upper(), logging.INFO)
            component_logger.setLevel(numeric_component_level)


# Default logger instance
default_logger = StructuredLogger("prompt_guard")


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(f"prompt_guard.{name}")


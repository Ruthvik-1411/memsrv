"""Helper functions for spans, attributes, decorators"""
import functools
import json
import logging
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from openinference.semconv.trace import SpanAttributes
from .constants import COMMON_ATTRIBUTES

logger = logging.getLogger(__name__)

# Global tracer reference (can be None)
_tracer = None

def init_tracer(tracer):
    """Called once during app startup to set global tracer instance."""
    global _tracer
    _tracer = tracer

def get_tracer():
    """Returns the global tracer or a no-op tracer."""
    return _tracer or trace.NoOpTracerProvider().get_tracer("noop")

def traced_span(name: str, kind: str = None, **static_attrs):
    """Decorator for async functions to add spans safely."""
    def decorator(func):
        if hasattr(func, "_is_traced"):  # prevent double wrapping
            return func

        # TODO: Add support for sync functions as well
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(name) as span:
                if kind:
                    span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, kind)
                for k, v in {**COMMON_ATTRIBUTES, **static_attrs}.items():
                    span.set_attribute(k, v)
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)

        func._is_traced = True
        return async_wrapper
    return decorator

def start_child_span(name: str, **attrs):
    """Manual span creation helper."""
    tracer = get_tracer()
    span = tracer.start_span(name)
    for k, v in attrs.items():
        span.set_attribute(k, v)
    return span

def safe_serialize(obj) -> str:
    """Convert an object to JSON safely (for attributes)."""
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)[:4000]
    except Exception:
        return "<not serializable>"

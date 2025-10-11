"""Helper functions for spans, attributes, decorators"""
import functools
import json
from pydantic import BaseModel

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from openinference.semconv.trace import SpanAttributes

from memsrv.utils.logger import get_logger
from .constants import COMMON_ATTRIBUTES

logger = get_logger(__name__)

# Global tracer reference (can be None)
_tracer = None

def init_tracer(tracer):
    """Called once during app startup to set global tracer instance."""
    global _tracer
    _tracer = tracer

def get_tracer():
    """Returns the global tracer or a no-op tracer."""
    return _tracer or trace.NoOpTracerProvider().get_tracer("noop")

def traced_span(name: str = None,
                kind: str = None,
                record_io: bool = True,
                **static_attrs):
    """Decorator for async functions to add spans safely."""
    def decorator(func):
        if hasattr(func, "_is_traced"):  # prevent double wrapping
            return func

        # TODO: Add support for sync functions as well later
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or func.__qualname__
            with tracer.start_as_current_span(span_name) as span:
                if kind:
                    span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, kind)
                for k, v in {**COMMON_ATTRIBUTES, **static_attrs}.items():
                    span.set_attribute(k, v)
                try:
                    if record_io:
                        call_args = args
                        # Skip self or cls args
                        if call_args and hasattr(call_args[0], "__class__"):
                            call_args = call_args[1:]
                        # If it's not key word arg, show it as arg0: val0
                        function_inputs = {
                            **{f"arg{i}": a for i, a in enumerate(call_args)},
                            **kwargs
                        }
                        span.set_attribute(SpanAttributes.INPUT_VALUE,
                                           safe_serialize(function_inputs))
                    
                    result = await func(*args, **kwargs)

                    if record_io:
                        span.set_attribute(SpanAttributes.OUTPUT_VALUE,
                                           safe_serialize(result))
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
    # Will be useful later
    tracer = get_tracer()
    span = tracer.start_span(name)
    for k, v in attrs.items():
        span.set_attribute(k, v)
    return span

def safe_serialize(obj, max_length: int = 4000) -> str:
    """Convert an object to JSON safely (for attributes)."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    def _convert(o):
        # Pydantic classes
        if isinstance(o, BaseModel):
            return o.model_dump()
        if isinstance(o, (str, int, float, bool, type(None))):
            return o
        if hasattr(o, "__class__") and not isinstance(o, (dict, list, tuple, set, BaseModel)):
            # Avoid trying to descend into defined classes
            # We can skip these args by filtering, but the check will be run all the time
            cls_name = o.__class__.__name__
            return f"<instance of {cls_name}>"
        # Common builtins
        if isinstance(o, (list, tuple, set)):
            return [_convert(i) for i in o]
        if isinstance(o, dict):
            return {k: _convert(v) for k, v in o.items()}

        return str(o)

    try:
        serialized = json.dumps(_convert(obj), ensure_ascii=False)
        return serialized[:max_length]
    except Exception as e:
        logger.error(f"Error serializing for tracing: {str(e)}.")
        return "<not serializable>"

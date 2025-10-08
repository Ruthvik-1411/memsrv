"""Telemetry setup for OpenTelemetry tracing support.
1) setup_tracer(): sets up the tracer provider and exporters.
2) traced_span(): decorator for instrumenting async functions.
3) start_child_span(): helper for manual child spans.
"""
from .setup import setup_tracer
from .tracing import traced_span, start_child_span
from .constants import CustomSpanNames, CustomSpanKinds

__all__ = [
    "setup_tracer",
    "traced_span",
    "start_child_span",
    "CustomSpanNames",
    "CustomSpanKinds"
]
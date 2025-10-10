"""Enrich common spans using helpers"""
from opentelemetry import trace
from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

from .tracing import safe_serialize

# TODO: use openinference kinds here
def trace_llm_call(provider: str,
                   model_name: str,
                   invocation_parameters: dict,
                   input_messages: list,
                   output_messages: list,
                   token_count: dict):
    """Adds standard attributes for an LLM span."""
    span = trace.get_current_span()
    span.set_attribute(SpanAttributes.LLM_MODEL_NAME, model_name)
    span.set_attribute(SpanAttributes.LLM_PROVIDER, provider)
    if invocation_parameters:
        span.set_attribute(SpanAttributes.LLM_INVOCATION_PARAMETERS, safe_serialize(invocation_parameters))

    if input_messages is not None:
        span.set_attribute(SpanAttributes.LLM_INPUT_MESSAGES, safe_serialize(input_messages))
    if output_messages is not None:
        span.set_attribute(SpanAttributes.LLM_OUTPUT_MESSAGES, safe_serialize(output_messages))

    # Token counts will be auto flat
    if token_count:
        for key, val in token_count.items():
            if isinstance(val, (int, float, str, bool)) or val is None:
                span.set_attribute(f"llm.token_count.{key}", val)

def trace_embedder_call(provider: str):
    """Adds standard attributes for an Embedder span."""
    span = trace.get_current_span()
    span.set_attribute(SpanAttributes.EMBEDDING_MODEL_NAME, provider)
    # Can add EMBEDDING_EMBEDDINGS = ["embds": [],"text":[]] but not needed

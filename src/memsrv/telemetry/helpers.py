"""Enrich common spans using helpers"""
# pylint: disable=too-many-positional-arguments
from typing import Literal, List, Dict, Any
from opentelemetry import trace
from openinference.semconv.trace import SpanAttributes

from .tracing import safe_serialize

def trace_llm_call(provider: str,
                   model_name: str,
                   invocation_parameters: dict,
                   system_instructions: str,
                   user_message: str,
                   output_message: str,
                   token_count: dict):
    """Adds standard attributes for an LLM span."""
    span = trace.get_current_span()
    span.set_attributes({
        SpanAttributes.INPUT_MIME_TYPE: "application/json",
        SpanAttributes.OUTPUT_MIME_TYPE: "application/json",
        SpanAttributes.LLM_MODEL_NAME: model_name,
        SpanAttributes.LLM_PROVIDER: provider
    })

    if invocation_parameters:
        span.set_attribute(SpanAttributes.LLM_INVOCATION_PARAMETERS,
                           safe_serialize(invocation_parameters))

    input_messages = [
        {
            "role": "system", "content": system_instructions
        },
        {
            "role": "user", "content": user_message
        }
    ]
    output_messages = [{"role": "model", "content": output_message}]

    span.set_attributes({
        **get_llm_message_attributes(input_messages, "input"),
        **get_llm_message_attributes(output_messages, "output")
    })

    # Token counts will be auto flat
    if token_count:
        for key, val in token_count.items():
            if isinstance(val, (int, float, str, bool)) or val is None:
                span.set_attribute(f"llm.token_count.{key}", val)

def trace_embedder_call(provider: str):
    """Adds standard attributes for an Embedder span."""
    span = trace.get_current_span()
    span.set_attribute(SpanAttributes.EMBEDDING_MODEL_NAME, provider)
    # NOTE: Can add EMBEDDING_EMBEDDINGS = ["embds": [],"text":[]] but not needed

def get_llm_message_attributes(messages: List[Dict[str, Any]],
                               message_type: Literal["input", "output"]) -> Dict[str, Any]:
    """
    Flattens a list of LLM messages into OpenInference-style span attributes.

    Args:
        messages: A list of {"role": str, "content": str} dicts.
        message_type: "input" or "output".

    Returns:
        A flat dict of span attributes like:
            {
                "llm.input_messages.0.role": "system",
                "llm.input_messages.0.content": "system instructions",
                "llm.input_messages.1.role": "user",
                "llm.input_messages.1.content": "user message"
            }
    Ref: openinference-instrumentation/src/openinference/instrumentation/_attributes.py#L419
    """
    # Note: We can use this lib: https://pypi.org/project/openinference-instrumentation/
    # to do the same thing, but why add more packages for simple utils which can be custom written
    if message_type not in ("input", "output"):
        raise ValueError("message_type must be 'input' or 'output'")

    base_key = f"llm.{message_type}_messages"
    attrs: Dict[str, Any] = {}

    if not isinstance(messages, list):
        return attrs

    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        content = msg.get("content")
        if role is not None:
            attrs[f"{base_key}.{i}.message.role"] = role
        if content is not None:
            attrs[f"{base_key}.{i}.message.content"] = content

    return attrs

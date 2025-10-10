"""Enrich common spans using helpers"""
from typing import Optional
from opentelemetry import trace
from openinference.semconv.trace import SpanAttributes

from .tracing import safe_serialize

# TODO: use openinference kinds here
def trace_llm_call(provider: str,
                   model_name: str,
                   invocation_parameters: dict,
                   system_instructions: str,
                   user_message: str,
                   output_message: str,
                   token_count: dict):
    """Adds standard attributes for an LLM span."""
    span = trace.get_current_span()
    span.set_attribute(SpanAttributes.LLM_MODEL_NAME, model_name)
    span.set_attribute(SpanAttributes.LLM_PROVIDER, provider)
    if invocation_parameters:
        span.set_attribute(SpanAttributes.LLM_INVOCATION_PARAMETERS,
                           safe_serialize(invocation_parameters))

    if user_message is not None:
        input_messages = safe_serialize(to_input_messages(user_message, system_instructions))
        span.set_attribute(SpanAttributes.LLM_INPUT_MESSAGES,
                           safe_serialize(input_messages))
        span.set_attribute("gen_ai.input.messages",safe_serialize(input_messages))
    if output_message is not None:
        output_messages = safe_serialize(to_output_messages(output_message))
        span.set_attribute(SpanAttributes.LLM_OUTPUT_MESSAGES,
                           output_messages)
        span.set_attribute("gen_ai.output.messages",output_messages)

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

def to_input_messages(user_message: str, system_instruction: Optional[str] = None):
    """Converts system instruction and user message to input_messages format."""
    messages = []

    if system_instruction:
        messages.append({
            "role": "system",
            "parts": [
                {
                    "type": "text",
                    "content": system_instruction
                }
            ]
        })

    messages.append({
        "role": "user",
        "parts": [
            {
                "type": "text",
                "content": user_message
            }
        ]
    })

    return messages

def to_output_messages(response_text: str, finish_reason: str = "stop"):
    """Converts response text to output_messages format."""
    return [
        {
            "role": "assistant",
            "parts": [
                {
                    "type": "text",
                    "content": response_text
                }
            ],
            "finish_reason": finish_reason
        }
    ]

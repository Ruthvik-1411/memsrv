"""Enrich common spans using helpers"""
from opentelemetry import trace
from .tracing import safe_serialize

# TODO: use openinference kinds here
def trace_llm_call(provider: str, model_name: str, invocation_parameters: dict, input_messages: list, output_messages: list, token_count: dict):
    """Adds standard attributes for an LLM span."""
    span = trace.get_current_span()
    span.set_attribute("llm.model_name", model_name)
    span.set_attribute("llm.provider", provider)
    if invocation_parameters:
        span.set_attribute("llm.invocation_parameters", safe_serialize(invocation_parameters))

    if input_messages is not None:
        span.set_attribute("llm.input_messages", safe_serialize(input_messages))
    if output_messages is not None:
        span.set_attribute("llm.output_messages", safe_serialize(output_messages))

    # Token counts will be auto flat
    if token_count:
        for key, val in token_count.items():
            if isinstance(val, (int, float, str, bool)) or val is None:
                span.set_attribute(f"llm.token_count.{key}", val)

def trace_db_call(query_type: str, table: str, rows_affected: int | None = None):
    """Adds attributes for DB-related spans."""
    span = trace.get_current_span()
    span.set_attribute("memsrv.operation", "db_call")
    span.set_attribute("memsrv.db.query_type", query_type)
    span.set_attribute("memsrv.db.table", table)
    if rows_affected is not None:
        span.set_attribute("memsrv.db.rows_affected", rows_affected)

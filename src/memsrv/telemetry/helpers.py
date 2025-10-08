"""Enrich common spans using helpers"""
from opentelemetry import trace
from .tracing import safe_serialize

# TODO: use openinference kinds here
def trace_llm_call(model: str, prompt, response, tokens_used: int | None = None):
    """Adds standard attributes for an LLM span."""
    span = trace.get_current_span()
    span.set_attribute("memsrv.operation", "llm_call")
    span.set_attribute("llm.model_name", model)
    span.set_attribute("llm.prompts", safe_serialize(prompt))
    span.set_attribute("llm.output_messages", safe_serialize(response))
    if tokens_used is not None:
        span.set_attribute("memsrv.llm.tokens_used", tokens_used)

def trace_db_call(query_type: str, table: str, rows_affected: int | None = None):
    """Adds attributes for DB-related spans."""
    span = trace.get_current_span()
    span.set_attribute("memsrv.operation", "db_call")
    span.set_attribute("memsrv.db.query_type", query_type)
    span.set_attribute("memsrv.db.table", table)
    if rows_affected is not None:
        span.set_attribute("memsrv.db.rows_affected", rows_affected)

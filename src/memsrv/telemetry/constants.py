"""Custom attribute and span kind mappings"""
from enum import Enum
# from opentelemetry.trace import SpanKind
# from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

class CustomSpanNames(str, Enum):
    """Custom span names as used in memsrv"""

    GENERATE_MEMORIES = "GenerateMemories"
    CREATE_MEMORIES = "CreateMemories"
    UPDATE_MEMORIES = "UpdateMemories"
    DELETE_MEMORIES = "DeleteMemories"

    FACT_EXTRACTION = "ExtractFacts"
    FACT_CONSOLIDATION = "ConsolidateFacts"

    DB_CREATE = "db.create"
    DB_UPDATE = "db.update"
    DB_DELETE = "db.delete"
    DB_QUERY_ID = "db.query.id"
    DB_QUERY_FILTER = "db.query.metadata"
    DB_QUERY_SIMILARITY = "db.query.similarity"

class CustomSpanKinds(str, Enum):
    DB = "DB"
    HTTP = "HTTP"
    BACKGROUND = "BACKGROUND"
    INTERNAL = "INTERNAL"
    MEMORY = "MEMORY"
    LLM = "LLM"
    CHAIN = "CHAIN"
    EMBEDDING = "EMBEDDING"
    RETRIEVER = "RETRIEVER"

COMMON_ATTRIBUTES = {
    "component": "memsrv",
    "library": "opentelemetry",
}

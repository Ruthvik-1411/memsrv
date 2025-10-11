"""Custom attribute and span kind mappings"""
from enum import Enum

class CustomSpanNames(str, Enum):
    """Custom span names as used in memsrv"""

    GENERATE_MEMORIES = "GenerateMemories"
    CREATE_MEMORIES = "CreateMemories"
    UPDATE_MEMORIES = "UpdateMemories"
    DELETE_MEMORIES = "DeleteMemories"

    FACT_EXTRACTION = "ExtractFacts"
    FACT_CONSOLIDATION_CHAIN = "ConsolidateFactsChain"
    FACT_CONSOLIDATION = "ConsolidateFacts"

    CREATE_MEMORIES_API = "[API] CreateMemoriesAPI"
    UPDATE_MEMORIES_API = "[API] UpdateMemoriesAPI"
    DELETE_MEMORIES_API = "[API] DeleteMemoriesAPI"

class CustomSpanKinds(str, Enum):
    """Custom span kinds used in memsrv, some common with OpenInference"""
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
    "service.name": "memsrv",
    "service.version": "1.0.0",
    "service.environment": "dev",
    "library": "opentelemetry"
}

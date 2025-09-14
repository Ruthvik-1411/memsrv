"""API response data models"""
from typing import Optional, Any, List, Dict, Literal
from pydantic import BaseModel

from memsrv.models.memory import MemoryMetadata

class QueryResponse(BaseModel):
    """Standard response model for database query operations."""
    ids: List[List[str]]
    documents: List[List[Optional[str]]]
    metadatas: List[List[Dict[str, Any]]]
    distances: Optional[List[List[float]]] = None

class MemoryResponse(BaseModel):
    """Model for a single memory returned to the client."""
    id: str
    document: str
    metadata: MemoryMetadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    similarity: Optional[float] = None

class GetMemoriesResponse(BaseModel):
    """Response model for any query that returns a list of memories."""
    memories: List[MemoryResponse]

class ActionConfirmation(BaseModel):
    """A generic confirmation for a successfully performed action on a memory."""
    # document here is for debugging, will be removed later since we might not
    # want to expose it in api response
    id: str
    document: Optional[str] = None
    status: Literal["CREATED", "UPDATED", "DELETED", "NOT_FOUND"]

class MemoriesActionResponse(BaseModel):
    """A generic response model for Create, Update, Delete operations."""
    message: str
    info: List[ActionConfirmation]

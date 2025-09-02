"""API response data models"""
from pydantic import BaseModel
from typing import Optional, List, Literal

from memsrv.models.memory import MemoryMetadata

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

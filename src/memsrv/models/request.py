"""API Request data models"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

from memsrv.models.memory import MemoryMetadata

class MemoryCreateRequest(BaseModel):
    """
    Model for the /memories/create endpoint.
    Client provides a list of documents and shared metadata.
    """
    documents: List[str] = Field(..., min_length=1, description="The text content of memory to add to memory service.")
    metadata: MemoryMetadata

class MemoryGenerateRequest(BaseModel):
    """
    Model for the /memories/generate endpoint.
    Client provides conversation history and shared metadata.
    """
    messages: List[Dict[str, Any]] = Field(description="List of messages altering between user and model as list role, parts")
    metadata: MemoryMetadata

class MemoryUpdateRequest(BaseModel):
    """
    Model for the /memories/update endpoint.
    Client provides the ID of the memory and the fields to update.
    Fields are optional to allow partial updates.
    """
    id: str = Field(description="ID of the memory to update")
    document: Optional[str] = None
    metadata: Optional[MemoryMetadata] = None

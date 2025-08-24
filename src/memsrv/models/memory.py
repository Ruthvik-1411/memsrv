"""data models for facts, memories and api services will be added here"""
import uuid
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

# TODO: add timestamps as well

class MemoryMetadata(BaseModel):
    user_id: str
    app_id: str
    session_id: str
    timestamp: Optional[str] = ""
    agent_name: str

class DBMemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document: str
    embedding: List[float]
    metadata: MemoryMetadata

# TODO: update with more fields as per design
class MemoryItem(BaseModel):
    fact_id: str
    fact: str
    metadata: Dict[str, Any]
    similarity: Optional[float] = 0.0

class GetMemoriesResponseModel(BaseModel):
    facts: List[MemoryItem]
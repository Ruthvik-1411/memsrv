"""data models for facts, memories and api services will be added here"""
from pydantic import BaseModel
from typing import Optional, Dict, List, Any

# TODO: add timestamps as well

class MemoryMetadata(BaseModel):
    user_id: str
    app_id: str
    session_id: str
    timestamp: Optional[str] = ""
    agent_name: str

# TODO: update with more fields as per design
class MemoryItem(BaseModel):
    fact_id: str
    fact: str
    metadata: Dict[str, Any]

class GetMemoriesResponseModel(BaseModel):
    facts: List[MemoryItem]
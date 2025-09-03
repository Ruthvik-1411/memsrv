"""API Request data models"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from pydantic.config import ConfigDict

from memsrv.models.memory import MemoryMetadata

class MemoryCreateRequest(BaseModel):
    """
    Model for the /memories/create endpoint.
    Client provides a list of documents and shared metadata.
    """
    documents: List[str] = Field(..., min_length=1, description="The text content of memory to add to memory service.")
    metadata: MemoryMetadata

    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "documents": ["I like john wick", "I love watching action movies"],
            "metadata": {
                "user_id": "user@email.com",
                "app_id": "swagger",
                "session_id": "s123",
                "agent_name": "custom_agent",
                "event_timestamp": "2025-08-29T17:35:10.557Z"
            }
        }]
    })

class MemoryGenerateRequest(BaseModel):
    """
    Model for the /memories/generate endpoint.
    Client provides conversation history and shared metadata.
    """
    messages: List[Dict[str, Any]] = Field(..., min_length=2, description="List of messages altering between user and model as list role, parts")
    metadata: MemoryMetadata

    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "messages": [
                { "role": "user", "parts": [{ "text": "hello" }]},
                { "role": "model", "parts": [{ "text": "Hello! How can I help you today?\n" }]},
                { "role": "user", "parts": [{ "text": "my name is ruths, i like action movies" }]},
                { "role": "model", "parts": [{"text": "Nice to meet you, Ruths. I like helping people. Do you have any questions for me?\n"}]}
            ],
            "metadata": {
                "user_id": "user@email.com",
                "app_id": "swagger",
                "session_id": "s123",
                "agent_name": "custom_agent",
                "event_timestamp": "2025-08-29T17:35:10.557Z"
            }
        }]
    })

class MemoryUpdateRequest(BaseModel):
    """
    Model for the /memories/update endpoint.
    Client provides the ID of the memory and the content to update.
    """
    id: str = Field(description="ID of the memory to update")
    document: str = Field(default=None, description="Memory text to update the existing one.")

    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "id": "be94116b-6817-4e87-b490-4adae1d7824b",
            "document": "I like action movies without CGI."
        }]
    })

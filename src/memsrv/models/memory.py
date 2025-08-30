"""data models for facts, memories and api services will be added here"""
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional, List

# TODO: add timestamps as well
def get_current_time():
    """Gets current UTC time in iso format"""
    # add offset based on timezone if needed
    return datetime.now(timezone.utc).isoformat()

class MemoryMetadata(BaseModel):
    """Metadata attached to a memory"""
    # we can use timestamp to track direct memory creation by llm using tools in same session
    user_id: str = Field(description="ID of the user to attach the memory to. e.g, user@email.com, u_123")
    app_id: str = Field(description="ID of the application acting as client for memory service.")
    session_id: str = Field(description="ID of the session to attach to the memory.")
    agent_name: str = Field(description="Name of the agent which is adding the memory or events originating from.")
    event_timestamp: Optional[str] = Field(default_factory=get_current_time, description="Time when the event occured in ISO format, if not provided server timestamp will be used")

    def filterable_dict(self) -> dict:
        """Return only the fields that can be used for filtering.
        This will help as the metadata fields grow
        Not used for now, since filters are get params now
        and partial values are allowed and timestamp_is not * field
        """
        return {
            "user_id": self.user_id,
            "app_id": self.app_id,
            "session_id": self.session_id,
            "agent_name": self.agent_name,
        }

class MemoryInDB(BaseModel):
    """A single memory record as stored in the database."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document: str
    embedding: List[float]
    metadata: MemoryMetadata
    created_at: str = Field(default_factory=get_current_time)
    updated_at: str = Field(default_factory=get_current_time)

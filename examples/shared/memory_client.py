"""Common http client side implementation for memory service"""
# pylint: disable=too-many-positional-arguments
import os
from typing import Dict, Any, List, Optional
import requests

MEMORY_SERVICE_URL = "http://localhost:8090/api/v1"

class MemoryClient:
    """Memory client that communicates with our memory service"""
    def __init__(self,
                 base_url: Optional[str] = MEMORY_SERVICE_URL,
                 user_id: Optional[str]=None,
                 app_id: Optional[str]=None):
        memory_service_url = base_url or os.getenv("MEMORY_SERVICE_URL")
        self.base_url = memory_service_url.rstrip("/")
        if user_id:
            self.user_id = user_id
        if app_id:
            self.app_id = app_id

    def add_to_memory(self,
                      messages: List[Dict[str, Any]],
                      metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds conversation messages + metadata to memory service.
        messages format: list of {role: str, content: str}, see events.json
        metadata: {user_id, session_id, app_id, agent_name, event_timestamp(opt)}
        """
        url = f"{self.base_url}/memories/generate"
        payload = {"messages": messages, "metadata": metadata}
        print(payload)
        response = requests.post(url, json=payload)
        # TODO: Need to add better reading of errors
        response.raise_for_status()
        return response.json()

    def create_memory(self,
                      memory_content: List[str],
                      metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds conversation messages + metadata to memory service.
        messages format: list of {role: str, content: str}, see events.json
        metadata: {user_id, session_id, app_id, agent_name, event_timestamp(opt)}
        """
        url = f"{self.base_url}/memories/create"
        payload = {"documents": memory_content, "metadata": metadata}
        print(payload)
        response = requests.post(url, json=payload)
        # TODO: Need to add better reading of errors
        response.raise_for_status()
        return response.json()

    def get_memories(self,
                     user_id: str,
                     session_id: Optional[str] = None,
                     app_id: Optional[str] = None,
                     limit: int = 50) -> Dict[str, Any]:
        """
        Fetch memories filtered by metadata.
        user_id, app_id are recommended to use always
        """
        url = f"{self.base_url}/memories"
        params = {
            "user_id": user_id,
            "session_id": session_id,
            "app_id": app_id,
            "limit": limit
        }
        response = requests.get(url,
                                params={key: value for key, value in params.items()
                                        if value is not None})
        # TODO: Need to add better reading of errors
        response.raise_for_status()
        return response.json()

    def get_similar_memories(self,
                             query: str,
                             user_id: str,
                             session_id: Optional[str] = None,
                             app_id: Optional[str] = None,
                             limit: int = 50) -> Dict[str, Any]:
        """
        Fetch similar memories filtered by metadata.
        query, user_id and app_id are recommended to be sent always
        """
        url = f"{self.base_url}/memories/similar"
        params = {
            "query": query,
            "user_id": user_id,
            "session_id": session_id,
            "app_id": app_id,
            "limit": limit
        }
        response = requests.get(url,
                                params={key: value for key, value in params.items()
                                        if value is not None})
        # TODO: Need to add better reading of errors
        response.raise_for_status()
        return response.json()

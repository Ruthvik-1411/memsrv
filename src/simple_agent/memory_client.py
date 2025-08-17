import requests
from typing import Dict, Any, List, Optional

class MemoryClient:
    def __init__(self, base_url: str = "http://localhost:8090/api/v1"):
        self.base_url = base_url.rstrip("/")

    def add_to_memory(self, messages: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds conversation messages + metadata to memory service.
        messages format: list of {role: str, content: str}, see events.json
        metadata: {user_id, session_id, app_id, agent_name, timestamp(opt)}
        """
        url = f"{self.base_url}/memories/generate"
        payload = {"messages": messages, "metadata": metadata}
        print(payload)
        response = requests.post(url, json=payload)
        # TODO: Need to add better reading of errors
        response.raise_for_status()
        return response.json()

    def get_memories(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        app_id: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Fetch memories filtered by metadata.
        """
        url = f"{self.base_url}/memories"
        params = {
            "user_id": user_id,
            "session_id": session_id,
            "app_id": app_id,
            "limit": limit
        }
        response = requests.get(url, params={key: value for key, value in params.items() if value is not None})
        # TODO: Need to add better reading of errors
        response.raise_for_status()
        return response.json()

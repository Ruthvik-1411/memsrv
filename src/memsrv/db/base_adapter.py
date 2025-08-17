"""Abstract class to add, query to vector DB"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorDBAdapter(ABC):
    """Abstract interface for any vector DB provider."""
    # Format filters might not always be required, but we'll see
    
    @abstractmethod
    def create_collection(self, name: str, metadata: Dict[str, Any] = None):
        """Create a new collection (or get it if exists)."""
        pass

    @abstractmethod
    def add(self, collection_name: str, items: List[Dict[str, Any]]):
        """Add items (facts + metadata) into a collection."""
        pass
    
    @abstractmethod
    def query_items(self, collection_name: str, filters: Dict[str, Any], limit: int = 5):
        """Query items by filters"""
        pass

    @abstractmethod
    def query_similar_items(self, collection_name: str, query_text: str, filters: Optional[Dict[str, Any]] = None, top_k: int = 20):
        """Query items by text with optional filters."""
        pass

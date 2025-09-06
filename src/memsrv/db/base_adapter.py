"""Abstract class to add, query to vector DB"""
# pylint: disable=unnecessary-pass, too-many-positional-arguments
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from memsrv.models.memory import MemoryInDB, MemoryUpdatePayload

class VectorDBAdapter(ABC):
    """Abstract interface for any vector DB provider."""
    # Format filters might not always be required, but we'll see

    @abstractmethod
    def create_collection(self,
                          name: str = "memories",
                          metadata: Optional[Dict[str, Any]] = None,
                          config: Optional[Dict[str, Any]] = None):
        """Create a new collection (or get it if exists)."""
        pass

    @abstractmethod
    async def add(self,
            collection_name: str,
            items: List[MemoryInDB]) -> List[str]:
        """Add items (facts + metadata) into a collection."""
        pass

    @abstractmethod
    async def update(self,
               collection_name: str,
               items: List[MemoryUpdatePayload]):
        """Updates items at given with new data, fact_id should be provided"""
        pass

    @abstractmethod
    async def delete(self,
               collection_name: str,
               fact_ids: List[str]):
        """Deletes items with provided id"""
        pass

    @abstractmethod
    async def get_by_ids(self,
                   collection_name: str,
                   ids: List[str]):
        """Get memory items by ids"""
        pass

    @abstractmethod
    async def query_by_filter(self,
                        collection_name: str,
                        filters: Dict[str, Any],
                        limit: int = 5):
        """Query items by filters"""
        pass

    @abstractmethod
    async def query_by_similarity(self,
                            collection_name: str,
                            query_embeddings: List[List[float]],
                            query_texts: List[Optional[str]] = None,
                            filters: Optional[Dict[str, Any]] = None,
                            top_k: int = 20):
        """Query items by text with optional filters."""
        pass

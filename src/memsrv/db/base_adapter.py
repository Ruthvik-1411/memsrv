"""Abstract class to add, query to vector DB"""
# pylint: disable=unnecessary-pass, too-many-positional-arguments
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from memsrv.models.memory import MemoryInDB, MemoryUpdatePayload

class VectorDBAdapter(ABC):
    """Abstract interface for any vector DB provider."""

    def __init__(self,
                 collection_name: str,
                 connection_string: Optional[str] = None,
                 persist_dir: Optional[str] = None):
        self.connection_string = connection_string
        self.persist_dir = persist_dir
        self.collection_name = collection_name

    @abstractmethod
    async def setup_database(self,
                             metadata: Optional[Dict[str, Any]] = None,
                             config: Optional[Dict[str, Any]] = None):
        """Class method to setup database during startup"""
        pass

    @abstractmethod
    async def create_collection(self,
                                collection_name: str,
                                metadata: Optional[Dict[str, Any]] = None,
                                config: Optional[Dict[str, Any]] = None):
        """Create a new collection (or get it if exists)."""
        pass

    @abstractmethod
    async def add(self,
                  items: List[MemoryInDB]) -> List[str]:
        """Add items (facts + metadata) into a collection."""
        pass

    @abstractmethod
    async def update(self,
                     items: List[MemoryUpdatePayload]):
        """Updates items at given with new data, fact_id should be provided"""
        pass

    @abstractmethod
    async def delete(self,
                     fact_ids: List[str]):
        """Deletes items with provided id"""
        pass

    @abstractmethod
    async def get_by_ids(self,
                         ids: List[str]):
        """Get memory items by ids"""
        pass

    @abstractmethod
    async def query_by_filter(self,
                              filters: Dict[str, Any],
                              limit: int = 5):
        """Query items by filters"""
        pass

    @abstractmethod
    async def query_by_similarity(self,
                                  query_embeddings: List[List[float]],
                                  query_texts: List[Optional[str]] = None,
                                  filters: Optional[Dict[str, Any]] = None,
                                  top_k: int = 20):
        """Query items by text with optional filters."""
        pass

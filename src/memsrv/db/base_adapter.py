"""Abstract class to add, query to vector DB"""
# pylint: disable=unnecessary-pass, too-many-positional-arguments
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from memsrv.models.memory import MemoryInDB, MemoryUpdatePayload
from memsrv.models.response import QueryResponse

class VectorDBAdapter(ABC):
    """Abstract interface for any vector DB provider."""

    def __init__(self,
                 collection_name: str,
                 description: str,
                 embedding_dim: str,
                 connection_string: Optional[str] = None,
                 persist_dir: Optional[str] = None,
                 provider_config: Optional[Dict[str, Any]] = None,
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 user: Optional[str] = None,
                 password: Optional[str] = None):
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.description = description
        self.connection_string = connection_string
        self.persist_dir = persist_dir
        self.provider_config = provider_config or {}
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    @abstractmethod
    async def setup_database(self):
        """Class method to setup database during startup"""
        pass

    @abstractmethod
    async def create_collection(self,
                                collection_name: str,
                                metadata: Optional[Dict[str, Any]] = None,
                                config: Optional[Dict[str, Any]] = None) -> bool:
        """Create a new collection (or get it if exists)."""
        pass

    @abstractmethod
    async def add(self,
                  items: List[MemoryInDB]) -> List[str]:
        """Add items (facts + metadata) into a collection."""
        pass

    @abstractmethod
    async def update(self,
                     items: List[MemoryUpdatePayload]) -> List[str]:
        """Updates items at given with new data, fact_id should be provided"""
        pass

    @abstractmethod
    async def delete(self,
                     fact_ids: List[str]):
        """Deletes items with provided id"""
        pass

    @abstractmethod
    async def get_by_ids(self,
                         ids: List[str]) -> QueryResponse:
        """Get memory items by ids"""
        pass

    @abstractmethod
    async def query_by_filter(self,
                              filters: Dict[str, Any],
                              limit: int = 5) -> QueryResponse:
        """Query items by filters"""
        pass

    @abstractmethod
    async def query_by_similarity(self,
                                  query_embeddings: List[List[float]],
                                  query_texts: List[Optional[str]] = None,
                                  filters: Optional[Dict[str, Any]] = None,
                                  top_k: int = 20) -> QueryResponse:
        """Query items by text with optional filters."""
        pass

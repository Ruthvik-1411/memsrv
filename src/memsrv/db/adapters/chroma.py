"""Chroma db implementation"""
import chromadb
from typing import List, Dict, Any, Optional
from memsrv.db.base_adapter import VectorDBAdapter
from memsrv.models.memory import DBMemoryItem

class ChromaDBAdapter(VectorDBAdapter):
    """Implements vector db ops for chroma DB"""
    def __init__(self, persist_dir: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_dir)
    
    def _format_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts simple {k: v} filter dict into Chroma's query format with $and + $eq.
        This formatter will be implemented for all adapters
        """
        if not filters:
            return {}
        if len(filters.items()) > 1:
            return {
                "$and": [
                    {key: {"$eq": value}}
                    for key, value in filters.items()
                ]
            }
        else:
            return filters

    def create_collection(self, name: str, metadata: Dict[str, Any] = None):
        """Create a chroma collection"""
        # We should use this when we want to fix and always use the same collection
        # In some cases we might create them based on request params, this will help
        # TODO: Change default configuration of L2 to cosine
        return self.client.get_or_create_collection(name=name, metadata=metadata)

    def add(self, collection_name: str, items: List[DBMemoryItem]):
        """Adds items to chromaDB.
        Args:
            List of items with keys id, document, embeddings, metadata(dict)
        """
        # TODO: Change default configuration of L2 to cosine
        collection = self.client.get_or_create_collection(name=collection_name)
        collection.add(
            ids=[item.id for item in items],
            documents=[item.document for item in items],
            embeddings=[item.embedding for item in items],
            metadatas=[item.metadata.dict() for item in items]
        )
        print(f"Successfully added {len(items)} items to chroma collection.")

    def query_by_filter(self, collection_name: str, filters: Dict[str, Any], limit = 20):
        """Retrieve by metadata filters only"""
        collection = self.client.get_collection(name=collection_name)
        where_clause = self._format_filters(filters)
        results = collection.get(
            where=where_clause if where_clause else None,
            limit=limit
        )
        return results

    def query_by_similarity(
        self, 
        collection_name: str,
        query_embedding: List[float],
        query_text: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None, 
        top_k: int = 5
    ):
        """Retreive items similar to query with optional filters"""

        collection = self.client.get_collection(name=collection_name)
        where_clause = self._format_filters(filters)

        # To keep our adapters clean, we expect embeddings independently
        # This way any provider can be used with any DB
        # In some cases for keyword search or to perform Hybrid search
        # we might use the query text
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause if where_clause else None
        )
        # Chroma supports multi queries in one call, so returns as a list of vals
        # Since we are currently running a single query, we take the first result
        if results.get("ids"):
            results["ids"] = results["ids"][0]
            results["documents"] = results["documents"][0]
            results["metadatas"] = results["metadatas"][0]
            results["distances"] = results["distances"][0]
        else:
            results["ids"], results["documents"], results["metadatas"], results["distances"] = [], [], [], []

        return results

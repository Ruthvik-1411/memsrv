"""Chroma db implementation"""
import chromadb
from typing import List, Dict, Any, Optional
from memsrv.db.base_adapter import VectorDBAdapter

class ChromaDBAdapter(VectorDBAdapter):
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
        return self.client.get_or_create_collection(name=name, metadata=metadata)

    def add(self, collection_name: str, items: List[Dict[str, Any]]):
        """Adds items to chromaDB.
        Args:
            List of items with keys id, document, embeddings, metadata(dict)
        """
        collection = self.client.get_or_create_collection(name=collection_name)
        collection.add(
            ids=[item["id"] for item in items],
            documents=[item["document"] for item in items],
            embeddings=[item["embedding"] for item in items],
            metadatas=[item.get("metadata", {}) for item in items]
        )
        print(f"Successfully added {len(items)} items to chroma collection.")

    def query_items(self, collection_name: str, filters: Dict[str, Any], limit = 20):
        """Retrieve by metadata filters only"""
        collection = self.client.get_collection(name=collection_name)
        where_clause = self._format_filters(filters)
        results = collection.get(
            where=where_clause if where_clause else None,
            limit=limit
        )
        return results
    
    def query_similar_items(
        self, 
        collection_name: str, 
        query_text: str, 
        filters: Optional[Dict[str, Any]] = None, 
        top_k: int = 5
    ):
        """Retreive items similar to query with optional filters"""
        # TODO: to use embeddings later
        collection = self.client.get_collection(name=collection_name)
        where_clause = self._format_filters(filters)
        results = collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where_clause if where_clause else None
        )
        return results

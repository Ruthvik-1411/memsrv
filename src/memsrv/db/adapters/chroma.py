"""Chroma db implementation"""
import chromadb
from typing import Dict, Any
from memsrv.db.base_adapter import VectorDBAdapter

class ChromaDBAdapter(VectorDBAdapter):
    """Implements vector db ops for chroma DB"""
    def __init__(self, persist_dir: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        # Create a collection with default setting
        # If there is a need to change the name, comment this and
        # call this method when initializing the adapter directly
        self.create_collection(
            name="memories",
            metadata={
                "description": "Collection for memory service"
            }
        )
    
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

    def create_collection(self, name, metadata):
        """Create a chroma collection"""
        # We should use this when we want to fix and always use the same collection
        # In some cases we might create them based on request params, this will help
        # TODO: Change default configuration of L2 to cosine
        self.client.get_or_create_collection(name=name, metadata=metadata)
        return True

    def add(self, collection_name, items):
        collection = self.client.get_collection(name=collection_name)
        collection.add(
            ids=[item.id for item in items],
            documents=[item.document for item in items],
            embeddings=[item.embedding for item in items],
            metadatas=[item.metadata.model_dump() for item in items]
        )
        print(f"Successfully added {len(items)} items to chroma collection.")
        return [item.id for item in items]
    
    def update(self, collection_name, items):
        collection = self.client.get_collection(name=collection_name)
        collection.update(
            ids=[item.id for item in items],
            documents=[item.document for item in items],
            embeddings=[item.embedding for item in items],
            metadatas=[item.metadata.model_dump() for item in items]
        )
        print(f"Successfully updated {len(items)} items to chroma collection.")
        return [item.id for item in items]

    def delete(self, collection_name, fact_ids):
        collection = self.client.get_collection(name=collection_name)
        collection.delete(ids=fact_ids)
        print(f"Successfully deleted memory with id {fact_ids} from chroma collection")
        return fact_ids

    def query_by_filter(self, collection_name, filters, limit):
        collection = self.client.get_collection(name=collection_name)
        where_clause = self._format_filters(filters)
        results = collection.get(
            where=where_clause if where_clause else None,
            limit=limit
        )
        return results

    def query_by_similarity(self, collection_name, query_embedding, query_text=None, filters=None, top_k=20):
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

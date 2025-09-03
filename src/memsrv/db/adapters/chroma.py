"""Chroma db implementation"""
from typing import Dict, Any
import chromadb
from memsrv.utils.logger import get_logger
from memsrv.db.base_adapter import VectorDBAdapter
from memsrv.db.utils import serialize_items

logger = get_logger(__name__)

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
        This formatter will be implemented for all adapters and changes as per
        the filtering mechanism of each adapter.
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
        serialized_items = serialize_items(items)
        
        collection.add(
            ids=serialized_items["ids"],
            documents=serialized_items["documents"],
            embeddings=serialized_items["embeddings"],
            metadatas=serialized_items["metadatas"]
        )
        
        logger.info(f"Successfully added {len(items)} items to chroma collection.")
        return serialized_items["ids"]
    
    def get_by_ids(self, collection_name, ids):

        collection = self.client.get_collection(name=collection_name)

        result = collection.get(ids=ids)

        return result

    def query_by_filter(self, collection_name, filters, limit):
        
        collection = self.client.get_collection(name=collection_name)
        where_clause = self._format_filters(filters)
        
        results = collection.get(
            where=where_clause if where_clause else None,
            limit=limit
        )

        return results

    def query_by_similarity(self, collection_name, query_embeddings, query_texts=None, filters=None, top_k=20):

        collection = self.client.get_collection(name=collection_name)
        where_clause = self._format_filters(filters)

        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=top_k,
            where=where_clause if where_clause else None
        )
        
        return results

    def update(self, collection_name, items):
        
        collection = self.client.get_collection(name=collection_name)
        ids_to_update = [item.id for item in items]
        documents = [item.document for item in items]
        embeddings = [item.embedding for item in items]
        metadatas = [{"updated_at": item.updated_at} for item in items]
        
        collection.update(
            ids=ids_to_update,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        logger.info(f"Successfully updated {len(items)} items to chroma collection.")
        return ids_to_update

    def delete(self, collection_name, fact_ids):
        
        collection = self.client.get_collection(name=collection_name)
        collection.delete(ids=fact_ids)
        
        logger.info(f"Successfully deleted memory with id {fact_ids} from chroma collection")
        return fact_ids

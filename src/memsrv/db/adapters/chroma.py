"""Chroma db implementation"""
# pylint: disable=too-many-positional-arguments, signature-differs
from typing import Dict, Any
import chromadb
from memsrv.utils.logger import get_logger
from memsrv.db.base_adapter import VectorDBAdapter
from memsrv.db.utils import serialize_items

logger = get_logger(__name__)

class ChromaDBAdapter(VectorDBAdapter):
    """Implements vector db ops for chroma DB"""
    def __init__(self, persist_dir: str = "./chroma_db"):

        # TODO: Use chroma client-server for true self-hosted service
        self.client = chromadb.PersistentClient(path=persist_dir)

    async def setup_database(self, name="memories", metadata=None, config=None):

        # TODO: Chrom returns 1-x value, we need x for similarity
        await self.create_collection(
            name=name,
            metadata={
                "description": "Collection for memory service"
            },
            config={
                "hnsw": {
                    "space": "cosine"
                    # more config as needed
                }
            }
        )
        return self

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

        return filters

    async def create_collection(self, name, metadata, config):

        logger.info("Ensuring chroma collection exists.")
        self.client.get_or_create_collection(name=name, metadata=metadata, configuration=config)

        return True

    async def add(self, collection_name, items):

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

    async def get_by_ids(self, collection_name, ids):

        collection = self.client.get_collection(name=collection_name)

        result = collection.get(ids=ids)

        return result

    async def query_by_filter(self, collection_name, filters, limit):

        collection = self.client.get_collection(name=collection_name)
        where_clause = self._format_filters(filters)

        results = collection.get(
            where=where_clause if where_clause else None,
            limit=limit
        )

        return results

    async def query_by_similarity(self,
                            collection_name,
                            query_embeddings,
                            query_texts=None,
                            filters=None,
                            top_k=20):

        collection = self.client.get_collection(name=collection_name)
        where_clause = self._format_filters(filters)

        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=top_k,
            where=where_clause if where_clause else None
        )

        return results

    async def update(self, collection_name, items):

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

    async def delete(self, collection_name, fact_ids):

        collection = self.client.get_collection(name=collection_name)
        collection.delete(ids=fact_ids)

        logger.info(f"Successfully deleted memory with id {fact_ids} from chroma collection")
        return fact_ids

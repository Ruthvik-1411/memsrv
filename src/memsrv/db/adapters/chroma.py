"""Chroma db implementation using client-server chroma setup"""
# pylint: disable=too-many-positional-arguments, signature-differs
from typing import Dict, Any
import chromadb
from memsrv.utils.logger import get_logger
from memsrv.db.base_adapter import VectorDBAdapter
from memsrv.db.utils import serialize_items
from memsrv.models.response import QueryResponse

from memsrv.telemetry.tracing import traced_span
from memsrv.telemetry.constants import CustomSpanKinds

logger = get_logger(__name__)

class ChromaDBAdapter(VectorDBAdapter):
    """Implements vector db ops for chroma DB via http client-server"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client_kwargs = {"host": self.host, "port": self.port}
        self.client = None

    async def setup_database(self):

        self.client = await chromadb.AsyncHttpClient(**self._client_kwargs)

        # TODO: Chrom returns 1-x value, we need x for similarity
        await self.create_collection(
            collection_name=self.collection_name,
            metadata={
                "description": self.description
            },
            config=self.provider_config or {"hnsw": {"space": "cosine"}}
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

    async def create_collection(self, collection_name, metadata, config):

        logger.info("Ensuring chroma collection exists.")
        await self.client.get_or_create_collection(name=collection_name,
                                                   metadata=metadata,
                                                   configuration=config)

        return True

    @traced_span(kind=CustomSpanKinds.DB.value)
    async def add(self, items):

        collection = await self.client.get_collection(name=self.collection_name)
        serialized_items = serialize_items(items)

        await collection.add(
            ids=serialized_items["ids"],
            documents=serialized_items["documents"],
            embeddings=serialized_items["embeddings"],
            metadatas=serialized_items["metadatas"]
        )

        logger.info(f"Successfully added {len(items)} items to chroma collection.")
        return serialized_items["ids"]

    @traced_span(kind=CustomSpanKinds.DB.value)
    async def get_by_ids(self, ids):

        collection = await self.client.get_collection(name=self.collection_name)

        results = await collection.get(ids=ids)

        return QueryResponse(
            ids=[results.get("ids", [])],
            documents=[results.get("documents", [])],
            metadatas=[results.get("metadatas", [])]
        )

    @traced_span(kind=CustomSpanKinds.DB.value)
    async def query_by_filter(self, filters, limit):

        collection = await self.client.get_collection(name=self.collection_name)
        where_clause = self._format_filters(filters)

        results = await collection.get(
            where=where_clause if where_clause else None,
            limit=limit
        )

        return QueryResponse(
            ids=[results.get("ids", [])],
            documents=[results.get("documents", [])],
            metadatas=[results.get("metadatas", [])]
        )

    @traced_span(kind=CustomSpanKinds.DB.value)
    async def query_by_similarity(self,
                                  query_embeddings,
                                  query_texts=None,
                                  filters=None,
                                  top_k=20):

        collection = await self.client.get_collection(name=self.collection_name)
        where_clause = self._format_filters(filters)

        results = await collection.query(
            query_embeddings=query_embeddings,
            n_results=top_k,
            where=where_clause if where_clause else None
        )

        return QueryResponse(
            ids=results.get("ids", []),
            documents=results.get("documents", []),
            metadatas=results.get("metadatas", []),
            distances=results.get("distances", [])
        )

    @traced_span(kind=CustomSpanKinds.DB.value)
    async def update(self, items):

        collection = await self.client.get_collection(name=self.collection_name)
        ids_to_update = [item.id for item in items]
        documents = [item.document for item in items]
        embeddings = [item.embedding for item in items]
        metadatas = [{"updated_at": item.updated_at} for item in items]

        await collection.update(
            ids=ids_to_update,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        logger.info(f"Successfully updated {len(items)} items to chroma collection.")
        return ids_to_update

    @traced_span(kind=CustomSpanKinds.DB.value)
    async def delete(self, fact_ids):

        collection = await self.client.get_collection(name=self.collection_name)
        await collection.delete(ids=fact_ids)

        logger.info(f"Successfully deleted memory with id {fact_ids} from chroma collection")
        return fact_ids

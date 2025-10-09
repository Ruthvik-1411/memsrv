"""Core MemoryService class to manage memories"""
# pylint: disable=too-many-locals, too-many-branches
from typing import List, Dict, Optional, Any, Union

from memsrv.core.extractor import parse_messages, extract_facts
from memsrv.llms.base_llm import BaseLLM
from memsrv.db.base_adapter import VectorDBAdapter
from memsrv.embeddings.base_embedder import BaseEmbedding
from memsrv.utils.logger import get_logger
from memsrv.models.memory import MemoryMetadata, MemoryInDB, MemoryUpdatePayload
from memsrv.models.request import MemoryCreateRequest, MemoryUpdateRequest
from memsrv.models.response import ActionConfirmation, MemoryResponse

from memsrv.core.consolidator import consolidate_facts
from opentelemetry import trace
from memsrv.telemetry.tracing import traced_span, safe_serialize
from memsrv.telemetry.constants import CustomSpanKinds, CustomSpanNames

logger = get_logger(__name__)

class MemoryService:
    """The core service that handles extraction and consolidation of memories"""
    def __init__(self, llm: BaseLLM, db_adapter: VectorDBAdapter, embedder: BaseEmbedding):
        """Initializes the MemoryService with dependency injection.

        Args:
            llm: An instance of a class that inherits from BaseLLM.
            db_adapter: An instance of a class that inherits from VectorDBAdapter.
            embedder: An instance of a class that inherits from BaseEmbeddingProvider.
        """
        self.llm = llm
        self.db = db_adapter
        self.embedder = embedder

    def _format_memory_response(self,
                               fact_id: str,
                               action: str,
                               fact_content: Optional[str]=None) -> ActionConfirmation:
        """Formats the action taken for memory"""
        return ActionConfirmation(
            id=fact_id,
            document=fact_content,
            status=action
        )

    async def get_memories_by_ids(self, memory_ids: List[str]) -> Dict[str, List[Any]]:
        """
        Retrieves memories for a given list of IDs.
        Returns a dict like:
        {
            "ids": ["id1", "id3"],
            "documents": [...],
            "metadatas": [...]
        }
        It only includes data for IDs that were actually found in the db.
        """

        return await self.db.get_by_ids(ids=memory_ids)

    @traced_span(CustomSpanNames.GENERATE_MEMORIES.value, kind=CustomSpanKinds.CHAIN.value)
    async def add_memories_from_conversation(self,
                                    messages: List,
                                    metadata: MemoryMetadata,
                                    consolidation: bool = True) -> list[str]:
        """Extracts facts from conversations and adds them to vector DB"""
        parsed_messages = parse_messages(messages)
        if not parsed_messages.strip():
            return []
        span = trace.get_current_span()
        span.set_attribute("memsrv.input.prompt", parsed_messages[:500])
        span.set_attribute("memsrv.input.metadata", safe_serialize(metadata))
        facts = await extract_facts(parsed_messages, self.llm)

        if not facts:
            return []

        if consolidation:
            response_action = await self.consolidate_and_add_memories(facts=facts,
                                                                      metadata=metadata)
        else:
            memories_to_create = MemoryCreateRequest(documents=facts, metadata=metadata)

            response_action = await self.create_memories(data=memories_to_create)

        return response_action

    @traced_span(CustomSpanNames.FACT_CONSOLIDATION_CHAIN.value, kind=CustomSpanKinds.CHAIN.value)
    async def consolidate_and_add_memories(self, facts: List[str], metadata: MemoryMetadata):
        """Adds memories to db after consolidating them"""

        filters = metadata.filterable_dict()
        similar_memories = await self.search_similar_memories(
            query_texts=facts,
            filters=filters,
            limit=3
        )

        # For first entries, we can directly create them
        if not similar_memories:
            logger.info("No similar memories found. \
                        Skipping consolidation and adding new facts directly.")
            create_request = MemoryCreateRequest(documents=facts, metadata=metadata)
            return await self.create_memories(create_request)

        similar_memories_dict = {}
        for memory in similar_memories:
            if memory.id not in similar_memories_dict:
                similar_memories_dict[memory.id] = {
                    "id": memory.id,
                    "document": memory.document
                }

        similar_memory_items = list(similar_memories_dict.values())

        temporary_id_map = {}

        for i, memory_item in enumerate(similar_memory_items):
            temporary_id_map[str(i)] = memory_item["id"]

        existing_memories = [
            { "id": str(i), "text": memory_item["document"]}
            for i, memory_item in enumerate(similar_memory_items)
        ]

        logger.info(f"New facts: {facts}")
        logger.info(f"Existing Memories: {existing_memories}")

        consolidation_result = await consolidate_facts(new_facts=facts,
                                                 existing_memories=existing_memories,
                                                 llm=self.llm)
        logger.info(f"Consolidation Plan: {consolidation_result.get('plan')}")
        memories_to_add = []
        memories_to_update = []
        memories_to_delete = []
        response_actions = []

        for plan_item in consolidation_result.get("plan", []):

            temporary_id = plan_item.get("id")
            text = plan_item.get("text")
            action = plan_item.get("action")

            if action == "CREATE":
                logger.info(f"Adding: {text}")
                memories_to_add.append(text)
            elif action == "UPDATE":
                if temporary_id in temporary_id_map:
                    original_id = temporary_id_map[temporary_id]
                    logger.info(f"Updating {original_id} with {text}")
                    memories_to_update.append(
                        MemoryUpdateRequest(
                            id=original_id,
                            document=text
                            # YAGNI: Ignore metadata for update
                            # create new one if needed
                        )
                    )
                else:
                    logger.error("Invalid `id` provided by llm, skipping updation.")
            elif action == "DELETE":
                if temporary_id in temporary_id_map:
                    original_id = temporary_id_map[temporary_id]
                    memories_to_delete.append(original_id)
                    logger.info(f"Deleting {original_id}")
                else:
                    logger.error("Invalid `id` provided by llm, skipping deletion.")

        if memories_to_add:
            create_request = MemoryCreateRequest(documents=memories_to_add,
                                                 metadata=metadata)
            response_actions.extend(await self.create_memories(create_request))

        if memories_to_update:
            response_actions.extend(await self.update_memories(memories_to_update))

        if memories_to_delete:
            response_actions.extend(await self.delete_memories(memories_to_delete))

        logger.info(response_actions)

        return response_actions

    @traced_span(CustomSpanNames.CREATE_MEMORIES.value, kind=CustomSpanKinds.CHAIN.value)
    async def create_memories(self, data: MemoryCreateRequest):
        """Directly creates memories and adds to DB"""

        facts = data.documents
        embeddings = await self.embedder.generate_embeddings(texts=facts)

        items: List[MemoryInDB] = [
            MemoryInDB(
                document=fact,
                embedding=embeddings[i],
                metadata=data.metadata
            )
            for i, fact in enumerate(facts)
        ]

        added_memories_id = await self.db.add(items=items)

        response = []
        for i, fact in enumerate(facts):
            response.append(
                self._format_memory_response(
                    fact_id=added_memories_id[i],
                    fact_content=fact,
                    action="CREATED"
                )
            )

        return response

    async def create_raw_memories(self, data: MemoryCreateRequest,
                               consolidation: bool = True):
        """Add memories directly from raw memory content after consolidation"""

        if consolidation:
            response_action = await self.consolidate_and_add_memories(data.documents,
                                                                      data.metadata)
            return response_action

        response_action = await self.create_memories(data=data)

        return response_action

    @traced_span(CustomSpanNames.UPDATE_MEMORIES.value, kind=CustomSpanKinds.CHAIN.value)
    async def update_memories(self, update_items: List[MemoryUpdateRequest]):
        """Updates memory with given id and fact content"""

        new_facts = [items.document for items in update_items]
        new_embeddings = await self.embedder.generate_embeddings(texts=new_facts)

        items: List[MemoryUpdatePayload] = [
            MemoryUpdatePayload(
                id=update_item.id,
                document=update_item.document,
                embedding=new_embeddings[i]
            )
            for i, update_item in enumerate(update_items)
        ]

        updated_memories_id = await self.db.update(items=items)

        response = []
        for i, item in enumerate(update_items):
            response.append(
                self._format_memory_response(
                    fact_id=updated_memories_id[i],
                    fact_content=item.document,
                    action="UPDATED"
                )
            )

        return response

    async def update_raw_memories(self, update_items: List[MemoryUpdateRequest]):
        """API facing update memories method, validates if ids exists and then updates"""
        item_ids = [update_item.id for update_item in update_items]

        existing_ids = await self.get_memories_by_ids(memory_ids=item_ids)

        items_to_update = []
        response_action = []
        partial_failure = False
        # TODO: check if set operation speeds up things here
        for item in update_items:
            if item.id in existing_ids.ids[0]:
                items_to_update.append(MemoryUpdateRequest(
                    id=item.id,
                    document=item.document
                ))
            else:
                partial_failure = True
                response_action.append(self._format_memory_response(
                    fact_id=item.id,
                    action="NOT_FOUND",
                    fact_content="DATA NOT FOUND"
                ))

        if items_to_update:
            response_action.extend(await self.update_memories(update_items=items_to_update))

        return response_action, partial_failure

    @traced_span(CustomSpanNames.DELETE_MEMORIES.value, kind=CustomSpanKinds.CHAIN.value)
    async def delete_memories(self, memory_ids: List[str]):
        """Delete memories from collection"""

        result = await self.db.delete(fact_ids=memory_ids)

        response = []
        for fact_id in result:
            response.append(
                self._format_memory_response(
                    fact_id=fact_id,
                    action="DELETED"
                )
            )

        return response

    async def delete_raw_memories_by_id(self, memory_ids: List[str]):
        """API facing method for deleting memories by id, validates them before deleting"""

        existing_ids = await self.get_memories_by_ids(memory_ids=memory_ids)

        ids_to_delete = []
        response_action = []
        partial_failure = False
        # TODO: check if set operation speeds up things here
        for mem_id in memory_ids:
            if mem_id in existing_ids.ids[0]:
                ids_to_delete.append(mem_id)
            else:
                partial_failure = True
                response_action.append(self._format_memory_response(
                    fact_id=mem_id,
                    action="NOT_FOUND",
                    fact_content="DATA NOT FOUND"
                ))

        if ids_to_delete:
            response_action.extend(await self.delete_memories(memory_ids=ids_to_delete))

        return response_action, partial_failure

    # TODO: Add delete by user_id and app_ids

    async def search_by_metadata(self, filters: Dict[str, Any] = None, limit: int = 20):
        """Queries vector db with provided filters"""

        results = await self.db.query_by_filter(filters=filters,
                                                limit=limit)

        memories = []
        for i in range(len(results.ids[0])):
            memories.append(
                MemoryResponse(
                    id=results.ids[0][i],
                    document=results.documents[0][i],
                    metadata=results.metadatas[0][i],
                    created_at=results.metadatas[0][i].get("created_at"),
                    updated_at=results.metadatas[0][i].get("updated_at")
                )
            )

        return memories

    @traced_span(kind=CustomSpanKinds.CHAIN.value)
    async def search_similar_memories(self,
                                      query_texts: Union[str, List[str]],
                                      filters: Dict[str, Any] = None,
                                      limit: int = 20):
        """Queries vector db and get memories similar to query and applies filters"""
        # FIXME: Since this accepts bulk operation, it should result in
        # [results1, results2...] but we just add everything to a single list for now
        if isinstance(query_texts, str):
            query_texts = [query_texts]

        query_embeddings = await self.embedder.generate_embeddings(texts=query_texts)

        results = await self.db.query_by_similarity(query_embeddings=query_embeddings,
                                                    filters=filters,
                                                    top_k=limit)
        memories = []

        for query_index in range(len(query_texts)): # pylint: disable=consider-using-enumerate
            ids = results.ids[query_index]
            documents = results.documents[query_index]
            metadatas = results.metadatas[query_index]
            distances = results.distances[query_index]

            for i in range(len(ids)): # pylint: disable=consider-using-enumerate
                memories.append(
                    MemoryResponse(
                        id=ids[i],
                        document=documents[i],
                        metadata=metadatas[i],
                        similarity=distances[i],
                        created_at=metadatas[i].get("created_at"),
                        updated_at=metadatas[i].get("updated_at")
                    )
                )

        return memories

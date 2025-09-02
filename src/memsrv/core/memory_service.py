"""To add MemoryService class to add facts and to db services"""
from typing import List, Dict, Optional, Any

from memsrv.core.extractor import parse_messages, extract_facts
from memsrv.llms.base_llm import BaseLLM
from memsrv.db.base_adapter import VectorDBAdapter
from memsrv.embeddings.base_embedder import BaseEmbedding
from memsrv.utils.logger import get_logger
from memsrv.models.memory import MemoryMetadata, MemoryInDB, MemoryUpdatePayload
from memsrv.models.request import MemoryCreateRequest, MemoryUpdateRequest
from memsrv.models.response import ActionConfirmation, MemoryResponse

from memsrv.core.consolidator import consolidate_facts

logger = get_logger(__name__)

class MemoryService:
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
    
    def format_memory_response(self, fact_id: str, action: str,  fact_content: Optional[str]=None) -> ActionConfirmation:
        """Formats the action taken for memory"""
        return ActionConfirmation(
            id=fact_id,
            document=fact_content,
            status=action
        )

    def add_facts_from_conversation(self, messages: List, metadata: MemoryMetadata, consolidate: bool = False) -> list[str]:
        """Extracts facts from conversations and adds them to vector DB"""
        parsed_messages = parse_messages(messages)
        if not parsed_messages.strip():
            return []

        facts = extract_facts(parsed_messages, self.llm)
        if not facts:
            return []
        
        if consolidate:
            response_action = self.add_memories(facts=facts, metadata=metadata)
        else:
            memories_to_create = MemoryCreateRequest(documents=facts, metadata=metadata)

            response_action = self.create_memories(data=memories_to_create)

        return response_action
    
    def search_memories_by_filter(self, filters: Dict[str, Any] = None, limit: int = 20):
        """Queries vector db with provided filters"""

        results = self.db.query_by_filter(collection_name="memories", filters=filters, limit=limit)
        memories = []
        for i in range(len(results.get("ids", []))):
            memories.append(
                MemoryResponse(
                    id=results["ids"][i],
                    document=results["documents"][i],
                    metadata=results["metadatas"][i],
                    created_at=results["metadatas"][i].get("created_at"),
                    updated_at=results["metadatas"][i].get("updated_at")
                )
            )
        
        return memories
    
    def search_memories_by_similarity(self, query: str, filters: Dict[str, Any] = None, limit: int = 20):
        """Queries vector db and get memories similar to query and applies filters"""
        query_embedding = self.embedder.generate_embeddings(texts=[query])

        results = self.db.query_by_similarity(collection_name="memories",
                                              query_embedding=query_embedding[0],
                                              filters=filters,
                                              top_k=limit)
        memories = []

        for i in range(len(results.get("ids", []))):
            memories.append(
                MemoryResponse(
                    id=results["ids"][i],
                    document=results["documents"][i],
                    metadata=results["metadatas"][i],
                    similarity=results["distances"][i],
                    created_at=results["metadatas"][i].get("created_at"),
                    updated_at=results["metadatas"][i].get("updated_at")
                )
            )
        return memories
    
    def create_memories(self, data: MemoryCreateRequest):
        """Directly creates memories and adds to DB"""

        facts = data.documents
        embeddings = self.embedder.generate_embeddings(texts=facts)

        items: List[MemoryInDB] = [
            MemoryInDB(
                document=fact,
                embedding=embeddings[i],
                metadata=data.metadata
            )
            for i, fact in enumerate(facts)
        ]
        
        added_memories_id = self.db.add(collection_name="memories", items=items)
        response = []
        for i, fact in enumerate(facts):
            response.append(
                self.format_memory_response(
                    fact_id=added_memories_id[i],
                    fact_content=fact,
                    action="CREATED"
                )
            )
        return response

    def delete_memories(self, memory_ids: List[str]):
        """Delete memories from collection"""
        result = self.db.delete(collection_name="memories", fact_ids=memory_ids)
        response = []
        for fact_id in result:
            response.append(
                self.format_memory_response(
                    fact_id=fact_id,
                    action="DELETED"
                )
            )
        return response
    
    def update_memories(self, update_items: List[MemoryUpdateRequest]):
        """Updates memory with given id and fact content"""
        
        new_facts = [items.document for items in update_items]
        new_embeddings = self.embedder.generate_embeddings(texts=new_facts)

        items: List[MemoryUpdatePayload] = [
            MemoryUpdatePayload(
                id=update_item.id,
                document=update_item.document,
                embedding=new_embeddings[i]
            )
            for i, update_item in enumerate(update_items)
        ]

        updated_memories_id = self.db.update(collection_name="memories", items=items)

        response = []
        for i, item in enumerate(update_items):
            response.append(
                self.format_memory_response(
                    fact_id=updated_memories_id[i],
                    fact_content=item.document,
                    action="UPDATED"
                )
            )
        return response

    def add_memories(self, facts: List[str], metadata: MemoryMetadata):
        """Adds memories to db after consolidating them"""

        similar_memories_dict = {}
        # TODO: Use batch similarity requests here
        # Since we can batch embed facts and batch query(chroma)
        # this seems to be most optmized path rather than embed and query
        # for each item
        for fact in facts:
            # For each fact find top 3 similar memories
            similar_memories = self.search_memories_by_similarity(
                query=fact,
                filters=metadata.filterable_dict(),
                limit=3
            )

            for similar_memory in similar_memories:
                # Add each existing memory to a dict and avoid repetition
                if similar_memory.id not in similar_memories_dict:
                    similar_memories_dict[similar_memory.id] = {
                        "id": similar_memory.id,
                        "document": similar_memory.document
                    }
        
        similar_memory_items = list(similar_memories_dict.values())

        temporary_id_map = {}

        for i, memory_item in enumerate(similar_memory_items):
            temporary_id_map[str(i)] = memory_item["id"]
        
        existing_memories = [
            { "id": str(i), "text": memory_item["document"]} for i, memory_item in enumerate(similar_memory_items)
        ]

        logger.info(f"New facts: {facts}")
        logger.info(f"Existing Memories: {existing_memories}")

        consolidation_result = consolidate_facts(new_facts=facts, existing_memories=existing_memories, llm=self.llm)
        logger.info(f"Final result: {consolidation_result.get('plan')}")
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
                            # Ignore metadata for update
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
            create_request = MemoryCreateRequest(documents=memories_to_add, metadata=metadata)
            response_actions.extend(self.create_memories(create_request))
            
        if memories_to_update:
            response_actions.extend(self.update_memories(memories_to_update))
            
        if memories_to_delete:
            response_actions.extend(self.delete_memories(memories_to_delete))
        
        logger.info(response_actions)
       
        return response_actions

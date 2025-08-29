"""To add MemoryService class to add facts and to db services"""
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional, Any

from memsrv.core.extractor import parse_messages, extract_facts
from memsrv.llms.base_llm import BaseLLM
from memsrv.db.base_adapter import VectorDBAdapter
from memsrv.embeddings.base_embedder import BaseEmbedding

from memsrv.models.memory import MemoryMetadata, MemoryInDB
from memsrv.models.request import MemoryCreateRequest, MemoryUpdateRequest
from memsrv.models.response import ActionConfirmation, MemoryResponse
load_dotenv()

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

    def add_facts_from_conversation(self, messages: List, metadata: MemoryMetadata) -> list[str]:
        """Extracts facts from conversations and adds them to vector DB"""
        parsed_messages = parse_messages(messages)
        if not parsed_messages.strip():
            return []

        facts = extract_facts(parsed_messages, self.llm)
        if not facts:
            return []

        embeddings = self.embedder.generate_embeddings(facts)

        items: List[MemoryInDB] = [
            MemoryInDB(
                document=fact,
                embedding=embeddings[i],
                metadata=metadata
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
    
    def search_memories_by_filter(self, filters: Dict[str, Any] = None, limit: int = 20):
        """Queries vector db with provided filters"""

        results = self.db.query_by_filter(collection_name="memories", filters=filters, limit=limit)
        memories = []
        for i in range(len(results.get("ids", []))):
            memories.append(
                MemoryResponse(
                    id=results["ids"][i],
                    document=results["documents"][i],
                    metadata=results["metadatas"][i]
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
                    similarity=results["distances"][i]
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

        # TODO: Partial update is allowed, either document or metadata or both
        # should update only those that are provided, validate if id exists as well
        items: List[MemoryInDB] = [
            MemoryInDB(
                id=update_item.id,
                document=update_item.document,
                embedding=new_embeddings[i],
                metadata=update_item.metadata
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

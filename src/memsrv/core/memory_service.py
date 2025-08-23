"""To add MemoryService class to add facts and to db services"""
import os
from dotenv import load_dotenv
from typing import List

from memsrv.core.extractor import parse_messages, extract_facts
from memsrv.llms.base_llm import BaseLLM
from memsrv.db.base_adapter import VectorDBAdapter
from memsrv.embeddings.base_embedder import BaseEmbedding
from memsrv.models.memory import MemoryMetadata, DBMemoryItem

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

    def add_facts_from_conversation(self, messages: list, metadata: MemoryMetadata) -> list[str]:
        parsed_messages = parse_messages(messages)
        if not parsed_messages.strip():
            return []

        facts = extract_facts(parsed_messages, self.llm)
        if not facts:
            return []

        embeddings = self.embedder.generate_embeddings(facts)

        items: List[DBMemoryItem] = [
            DBMemoryItem(
                document=fact,
                embedding=embeddings[i],
                metadata=metadata
            )
            for i, fact in enumerate(facts)
        ]
        
        self.db.add(collection_name="memories", items=items)
        return facts
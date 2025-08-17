"""To add MemoryService class to add facts and to db services"""
import os
from dotenv import load_dotenv
from memsrv.llms.gemini import GeminiModel
from memsrv.llms.base_config import BaseLLMConfig
from memsrv.models.memory import MemoryMetadata
from memsrv.core.extractor import parse_messages, extract_facts
from memsrv.db.adapters.chroma import ChromaDBAdapter
load_dotenv()

class MemoryService:
    def __init__(self, model_name: str = "gemini-2.0-flash", api_key: str=None):
        config = BaseLLMConfig(
            model_name=model_name,
            api_key=api_key or os.getenv("GOOGLE_API_KEY")
        )
        # TODO: Should choose based on model provided or config values
        self.llm = GeminiModel(config)
        self.db = ChromaDBAdapter()

    def add_facts_from_conversation(self, messages: list, metadata: MemoryMetadata) -> list[str]:
        parsed_messages = parse_messages(messages)
        facts = extract_facts(parsed_messages, self.llm)
        print(facts)

        items = [
            {
                "id": f"{metadata.session_id}-{i}",
                "document": fact,
                # TODO: Provide the embedding function later
                "embedding": [1.1, 1.2, 1.3],
                "metadata": metadata.model_dump()
            }
            for i, fact in enumerate(facts)
        ]
        self.db.add(collection_name="memories", items=items)

        return facts
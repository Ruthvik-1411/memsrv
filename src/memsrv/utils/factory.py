"""All provider factories (LLM, DB, Embeddings) will be created here"""

import importlib
from typing import Any, Type

# Once a service is deployed we use only those config throughout
from config import memory_config
from memsrv.llms.base_config import BaseLLMConfig
from memsrv.llms.base_llm import BaseLLM
from memsrv.embeddings.base_embedder import BaseEmbedding
from memsrv.db.base_adapter import VectorDBAdapter
from memsrv.core.memory_service import MemoryService

def load_class(path: str) -> Type[Any]:
    """Dynamically import a class from a full path string"""
    # This helps in lazy loading
    module_path, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

class LLMFactory:
    """Factory for creating LLM instances"""

    provider_mapping = {
        "gemini": "memsrv.llms.providers.gemini.GeminiModel",
    }

    @classmethod
    def create(cls) -> BaseLLM:
        """Creates the llm instance using the config"""
        provider = memory_config.LLM_PROVIDER
        model_name = memory_config.LLM_MODEL

        if provider not in cls.provider_mapping:
            raise ValueError(f"Unsupported LLM provider: {provider}.")

        llm_class = load_class(cls.provider_mapping[provider])
        config = BaseLLMConfig(model_name=model_name,
                               api_key=memory_config.LLM_API_KEY)

        return llm_class(config)

class EmbeddingFactory:
    """Factory for creating embedding instances"""

    provider_mapping = {
        "gemini": "memsrv.embeddings.providers.gemini.GeminiEmbedding",
    }

    @classmethod
    def create(cls) -> BaseEmbedding:
        """Creates the embedding instance using the config"""
        provider = memory_config.EMBEDDING_PROVIDER
        model_name = memory_config.EMBEDDING_MODEL

        if provider not in cls.provider_mapping:
            raise ValueError(f"Unsupported Embedding provider: {provider}.")

        embedder_class = load_class(cls.provider_mapping[provider])
        # FIXME: Using llm key for now but should seperate later
        return embedder_class(model_name=model_name, api_key=memory_config.LLM_API_KEY)

class DBFactory:
    """Factory for creating database adapter instances"""

    provider_mapping = {
        "chroma": "memsrv.db.adapters.chroma.ChromaDBAdapter",
        "postgres": "memsrv.db.adapters.postgres.PostgresDBAdapter",
    }

    @classmethod
    async def create(cls) -> VectorDBAdapter:
        """Creates the db adapter instance using the config"""
        provider = memory_config.DB_PROVIDER

        if provider not in cls.provider_mapping:
            raise ValueError(f"Unsupported DB provider: {provider}.")

        db_class = load_class(cls.provider_mapping[provider])
        db_instance = db_class(**memory_config.DB_CONFIG)
        
        return await db_instance.setup_database()

class MemoryServiceFactory:
    """Factory for creating MemoryService"""

    @classmethod
    async def create(cls) -> MemoryService:
        """
        Creates the memory service instance by creating all
        the llm, embedding and db instances using the config
        """
        llm_instance = LLMFactory.create()
        embedder_instance = EmbeddingFactory.create()
        db_instance = await DBFactory.create()

        return MemoryService(
            llm=llm_instance,
            db_adapter=db_instance,
            embedder=embedder_instance,
        )

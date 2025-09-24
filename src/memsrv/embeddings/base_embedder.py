"""Base class for embeddings"""
# pylint: disable=unnecessary-pass
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union

from memsrv.embeddings.base_config import BaseEmbeddingConfig

class BaseEmbedding(ABC):
    """Abstract interface for any embedding model provider."""
    def __init__(self,
                 config: Optional[Union[BaseEmbeddingConfig, Dict]]=None):
        if isinstance(config, dict):
            self.config = BaseEmbeddingConfig(**config)
        elif isinstance(config, BaseEmbeddingConfig):
            self.config = config
        else:
            raise ValueError("Missing config when intializing embedding service")

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of texts."""
        pass

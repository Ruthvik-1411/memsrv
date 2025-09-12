"""Base class for embeddings"""
# pylint: disable=unnecessary-pass
from abc import ABC, abstractmethod
from typing import List

class BaseEmbedding(ABC):
    """Abstract interface for any embedding model provider."""
    def __init__(self,
                 model_name: str,
                 api_key: str):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of texts."""
        pass

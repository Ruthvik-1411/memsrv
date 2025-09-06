"""Base class for embeddings"""
# pylint: disable=unnecessary-pass
from abc import ABC, abstractmethod
from typing import List

class BaseEmbedding(ABC):
    """Abstract interface for any embedding model provider."""

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of texts."""
        pass

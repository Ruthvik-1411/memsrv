"""Embeddings generator using google embeds"""
from typing import List
from google.genai.client import Client as geminiClient
from google.genai.types import EmbedContentConfig
from memsrv.utils.logger import get_logger
from memsrv.embeddings.base_embedder import BaseEmbedding

logger = get_logger(__name__)

class GeminiEmbedding(BaseEmbedding):
    """Embedding module for generating embeddings using gemini api"""
    def __init__(self, model_name: str = "gemini-embedding-001", api_key: str = None):
        self.embedding_model_name = model_name
        self.client = geminiClient(api_key=api_key)

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of texts using Gemini embedding models."""
        try:
            embedding_result = []
            result = await self.client.aio.models.embed_content(
                model=self.embedding_model_name,
                contents=texts,
                config=EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=768
                )
            )
            for embedding in result.embeddings:
                embedding_result.append(embedding.values)
            return embedding_result
        except Exception as e:
            logger.error(f"An error occurred during embedding generation: {e}")
            return [[] for _ in texts]

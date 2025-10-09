"""Embeddings generator using google embeds"""
from typing import List, Optional
from google.genai.client import Client as geminiClient
from google.genai.types import EmbedContentConfig
from memsrv.utils.logger import get_logger
from memsrv.embeddings.base_embedder import BaseEmbedding
from memsrv.embeddings.base_config import BaseEmbeddingConfig

from memsrv.telemetry.tracing import traced_span
from memsrv.telemetry.constants import CustomSpanKinds, CustomSpanNames

logger = get_logger(__name__)

class GeminiEmbedding(BaseEmbedding):
    """Embedding module for generating embeddings using gemini api"""
    def __init__(self, config: Optional[BaseEmbeddingConfig]=None):
        super().__init__(config=config)
        self.client = geminiClient(api_key=self.config.api_key)
    
    @traced_span(kind=CustomSpanKinds.EMBEDDING.value)
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of texts using Gemini embedding models."""
        try:
            embedding_result = []
            result = await self.client.aio.models.embed_content(
                model=self.config.model_name,
                contents=texts,
                config=EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=self.config.embedding_dims
                )
            )
            for embedding in result.embeddings:
                embedding_result.append(embedding.values)
            return embedding_result
        except Exception as e:
            logger.error(f"An error occurred during embedding generation: {e}")
            return [[] for _ in texts]

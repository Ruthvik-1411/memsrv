"""Embeddings generator using google embeds"""
from typing import List, Optional
from google.genai.client import Client as geminiClient
from google.genai.types import EmbedContentConfig

from memsrv.embeddings.base_embedder import BaseEmbedding
from memsrv.embeddings.base_config import BaseEmbeddingConfig

from memsrv.telemetry.constants import CustomSpanKinds
from memsrv.telemetry.tracing import traced_span
from memsrv.telemetry.helpers import trace_embedder_call
from memsrv.utils.logger import get_logger
from memsrv.utils.retry import retry_with_backoff, rate_limited

logger = get_logger(__name__)

class GeminiEmbedding(BaseEmbedding):
    """Embedding module for generating embeddings using gemini api"""
    def __init__(self, config: Optional[BaseEmbeddingConfig]=None):
        super().__init__(config=config)
        self.client = geminiClient(api_key=self.config.api_key)

    @traced_span(kind=CustomSpanKinds.EMBEDDING.value)
    @rate_limited(calls_per_second=2.0)
    @retry_with_backoff(max_retries=3, base_delay=1, max_delay=8)
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

            trace_embedder_call(provider=self.config.model_name)

            return embedding_result
        except Exception as e:
            logger.error(f"An error occurred during embedding generation: {e}")
            return [[] for _ in texts]

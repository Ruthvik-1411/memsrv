"""Base class for embedding config parameters"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class BaseEmbeddingConfig:
    """Base config for embedding parameters"""
    model_name: str
    api_key: str
    embedding_dims: Optional[int] = 768

"""Base class for llms config parameters"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class BaseLLMConfig:
    """Base config for LLM parameters"""
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.1
    max_output_tokens: int = 1024
    top_p: float = 0.1
    top_k: float = 1

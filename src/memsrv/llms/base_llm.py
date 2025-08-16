from abc import ABC, abstractmethod
from typing import Dict, Optional, Union

from memsrv.llms.base_config import BaseLLMConfig

class BaseLLM(ABC):
    """Base class for all LLMs"""
    def __init__(self,
                 config: Optional[Union[BaseLLMConfig, Dict]]=None):
        if isinstance(config, dict):
            self.config = BaseLLMConfig(**config)
        elif isinstance(config, BaseLLMConfig):
            self.config = config
        else:
            self.config = BaseLLMConfig()

    @abstractmethod
    def generate_response(self, *args, **kwargs):
        """Generates a response from the model"""
        pass

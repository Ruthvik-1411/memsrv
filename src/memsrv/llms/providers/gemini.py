"""generic classes to use gemini api providers"""
import os
from typing import Optional
from google.genai import types
from google.genai.client import Client as geminiClient
from memsrv.llms.base_config import BaseLLMConfig
from memsrv.llms.base_llm import BaseLLM

class GeminiModel(BaseLLM):
    """Generation module for invoking gemini API"""
    def __init__(self, config: Optional[BaseLLMConfig]=None):
        super().__init__(config)

        if not self.config.model_name:
            self.config.model_name = "gemini-2.0-flash"

        api_key = self.config.api_key or os.getenv("GOOGLE_API_KEY")
        self.client = geminiClient(api_key=api_key)

    async def generate_response(self,
                          message: str,
                          system_instruction: str = None,
                          response_format=None):

        contents = []
        contents.append(
            types.Content(
                parts=[types.Part(text=message)],
                role="user"
            )
        )

        generation_config = {
            "temperature": self.config.temperature,
            "max_output_tokens": self.config.max_output_tokens,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k
        }

        if system_instruction:
            generation_config["system_instruction"] = system_instruction

        if response_format:
            generation_config["response_mime_type"] = "application/json"
            generation_config["response_schema"] = response_format

        response = await self.client.aio.models.generate_content(
            model=self.config.model_name,
            config=types.GenerateContentConfig(**generation_config),
            contents=contents
        )

        if hasattr(response, "text") and response.text:
            return response.text

        if hasattr(response, "candidates") and response.candidates:
            parts = response.candidates[0].content.parts
            if parts and hasattr(parts[0], "text"):
                return parts[0].text

        return "empty response"

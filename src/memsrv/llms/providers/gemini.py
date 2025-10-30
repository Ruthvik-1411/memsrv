"""generic classes to use gemini api providers"""
from typing import Optional
from google.genai import types
from google.genai.client import Client as geminiClient
from google.genai.errors import APIError as GeminiAPIError

from memsrv.llms.base_config import BaseLLMConfig
from memsrv.llms.base_llm import BaseLLM

from memsrv.utils.logger import get_logger
from memsrv.utils.retry import retry_with_backoff, rate_limited
from memsrv.utils.exceptions import APIError, RetryableAPIError, ConfigurationError

from memsrv.telemetry.constants import CustomSpanKinds
from memsrv.telemetry.tracing import traced_span
from memsrv.telemetry.helpers import trace_llm_call

logger = get_logger(__name__)

class GeminiModel(BaseLLM):
    """Generation module for invoking gemini API"""
    def __init__(self, config: Optional[BaseLLMConfig]=None):
        super().__init__(config)

        if not self.config.model_name:
            self.config.model_name = "gemini-2.0-flash"

        api_key = self.config.api_key
        self.client = geminiClient(api_key=api_key)

    @traced_span(kind=CustomSpanKinds.LLM.value)
    @rate_limited(calls_per_second=2.0)
    @retry_with_backoff(max_retries=3,
                        base_delay=1,
                        max_delay=8,
                        retry_on_exceptions=(RetryableAPIError,))
    async def generate_response(self,
                                message: str,
                                system_instruction: str = None,
                                response_format=None) -> str:

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

        try:
            response = await self.client.aio.models.generate_content(
                model=self.config.model_name,
                config=types.GenerateContentConfig(**generation_config),
                contents=contents
            )
        except GeminiAPIError as e:
            # https://ai.google.dev/gemini-api/docs/troubleshooting
            logger.warning(
                f"Gemini API call failed with status '{e.status}'."
                "Translating to custom exception."
            )

            if getattr(e, 'status', None) == "PERMISSION_DENIED":
                raise ConfigurationError(
                    f"Gemini API permission denied. Check the config. {e.message}"
                ) from e

            if getattr(e, 'status', None) in ["INVALID_ARGUMENT", "NOT_FOUND"]:
                raise ConfigurationError(f"Invalid argument sent to Gemini API. {e.message}") from e

            if getattr(e, 'status', None) in ["RESOURCE_EXHAUSTED", "UNAVAILABLE", "INTERNAL"]:
                raise RetryableAPIError(
                    f"Gemini API is temporarily unavailable ({e.status}). {e.message}"
                ) from e

            raise APIError(f"Unexpected Gemini API error occurred ({e.status}),{e.message}") from e

        usage_data = {
            "prompt": response.usage_metadata.prompt_token_count,
            "completion": response.usage_metadata.candidates_token_count,
            "total": response.usage_metadata.total_token_count
        }
        if hasattr(response, "text") and response.text:
            trace_llm_call(provider="gemini",
                           model_name=self.config.model_name,
                           invocation_parameters=generation_config,
                           system_instructions=system_instruction,
                           user_message=message,
                           output_message=response.text,
                           token_count=usage_data)
            return response.text

        raise APIError("LLM returned a successful but empty response.")

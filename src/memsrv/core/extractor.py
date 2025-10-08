"""Extracts facts from conversations using llms"""
from pydantic import BaseModel, Field
from memsrv.llms.base_llm import BaseLLM
from memsrv.core.prompts import FACT_EXTRACTION_PROMPT

from memsrv.telemetry.tracing import traced_span
from memsrv.telemetry.constants import CustomSpanKinds, CustomSpanNames

class Facts(BaseModel):
    """Pydantic models for facts extracted from conversation"""
    facts: list[str] = Field(description="The facts about the user from the conversation")

def parse_messages(messages: list) -> str:
    """Parses list of messages and formats them into format
        User: text\nAssistant: text\nUser: ...
    Ignores function calls and responses
    Args:
        messages(list): List of messages between user and model
        see events.json for expected structure
    Returns:
        conversation string in the above format
    """
    parsed_result = []
    for message in messages:
        role = message.get("role")
        for part in message.get("parts", []):
            if "text" in part:
                text = part["text"].strip()
                if role == "user":
                    parsed_result.append(f"User: {text}")
                elif role == "model":
                    parsed_result.append(f"Assistant: {text}")
    return "\n".join(parsed_result)

@traced_span(CustomSpanNames.FACT_EXTRACTION.value, CustomSpanKinds.BACKGROUND.value)
async def extract_facts(parsed_messages: str, llm: BaseLLM) -> list[str]:
    """Extracts facts using the provided LLM"""
    response = await llm.generate_response(
        system_instruction=FACT_EXTRACTION_PROMPT,
        message="Now, extract the facts from the following conversation:\n" + parsed_messages,
        response_format=Facts.model_json_schema()
    )

    parsed_facts_obj = Facts.model_validate_json(response)

    return parsed_facts_obj.facts

"""Consolidates facts with existing facts using LLM"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

from memsrv.llms.base_llm import BaseLLM
from memsrv.core.prompts import FACT_CONSOLIDATION_PROMPT

from memsrv.utils.logger import get_logger

logger = get_logger(__name__)

class Action(Enum):
    """Allowed memory actions"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    NOOP = "NOOP"

class ConsolidationPlanItem(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(description="ID of the original memory if it's part of the existing memory, if new fact a unique value")
    text: str = Field(description="The text content of the latest fact to consider")
    action: Action = Field(description="The action to be taken")
    old_text: Optional[str] = Field(description="The old text of the memory in case of updation", default=None)

class ConsolidationPlan(BaseModel):
    plan: List[ConsolidationPlanItem]


def consolidate_facts(new_facts: List[str], existing_memories: List[Dict[str, Any]], llm: BaseLLM) -> list[str]:
    """Extracts facts using the provided LLM and provides a consolidation plan"""

    message = f"""Now, consolidate the facts using the following input:
1. EXISTING_MEMORIES: List of existing memories with `id` and `text`.
{existing_memories}

2. NEW_FACTS: A list of new facts to process.
{new_facts}

"""
    logger.info(message)

    response = llm.generate_response(
        system_instruction=FACT_CONSOLIDATION_PROMPT,
        message = message,
        response_format=ConsolidationPlan.model_json_schema()
    )

    logger.info(response)
    parsed_facts_obj = ConsolidationPlan.model_validate_json(response)

    return parsed_facts_obj.model_dump(exclude_none=True)
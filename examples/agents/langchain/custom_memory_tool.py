"""A custom implementation for PreLoadMemoryTool() of google-adk but for langchain"""
from typing import Optional
from langchain_core.messages import SystemMessage
from langchain.agents.middleware import AgentState
from langgraph.runtime import Runtime

from shared.memory_client import MemoryClient
from .prompt import BASE_SYSTEM_INSTRUCTIONS

memory = MemoryClient()

class CustomAgentState(AgentState):
    """Custom agent state variables to manage metadata"""
    user_id: str
    app_name: str
    remaining_steps: Optional[str] = None

# 1. Using a callable to dynamically inject memory context into system instructions
def preload_memory_prompt(state):
    """Intervenes in an llm request and injects memories into context"""

    user_id = state.get("user_id")
    app_name = state.get("app_name")
    memory_text = ""
    try:
        raw_user_memories = memory.get_memories(user_id=user_id,
                                                app_id=app_name)

        if not raw_user_memories["memories"]:
            system_msg = SystemMessage(BASE_SYSTEM_INSTRUCTIONS)
            return [system_msg] + state["messages"]

        # memory_text = "My name is ruths. I like action movies." # For testing
        for item in raw_user_memories["memories"]:
            memory_text += item["document"] + "\n"

        memory_context = f"""The following content is from your previous conversations with the user.
They may be useful for answering the user's current query.
<PAST_CONVERSATIONS>
{memory_text}
</PAST_CONVERSATIONS>
"""
        # Append memory related context to system instructions
        system_msg = SystemMessage(BASE_SYSTEM_INSTRUCTIONS + memory_context)
        return [system_msg] + state["messages"]

    except Exception as e:
        print(f"Error occured fetching memories: {str(e)}. Proceeding without long-term-memory.")
        system_msg = SystemMessage(BASE_SYSTEM_INSTRUCTIONS)
        return [system_msg] + state["messages"]

# 2. Using middleware callable to dynamically inject memory context into system instructions
def preload_memory_prompt_for_middleware(state: AgentState,
                                         runtime: Runtime[CustomAgentState]) -> str:
    """Intervenes in an llm request and injects memories into context"""
    context = runtime.context

    if not context:
        return BASE_SYSTEM_INSTRUCTIONS

    user_id = context.get("user_id")
    app_name = context.get("app_name")

    if not user_id or not app_name:
        return BASE_SYSTEM_INSTRUCTIONS

    memory_text = ""
    try:
        raw_user_memories = memory.get_memories(user_id=user_id,
                                                app_id=app_name)
        if not raw_user_memories or not raw_user_memories.get("memories"):
            return BASE_SYSTEM_INSTRUCTIONS

        # memory_text = "My name is ruths. I like action movies.\n"
        for item in raw_user_memories["memories"]:
            memory_text += item["document"] + "\n"

        memory_context = f"""The following content is from your previous conversations with the user.
They may be useful for answering the user's current query.
<PAST_CONVERSATIONS>
{memory_text}
</PAST_CONVERSATIONS>
"""
        # Append memory related context to system instructions
        return BASE_SYSTEM_INSTRUCTIONS + memory_context

    except Exception as e:
        print(f"Error occurred fetching memories: {str(e)}. Proceeding without long-term-memory.")
        return BASE_SYSTEM_INSTRUCTIONS

# [WIP]: If langchain breaks, it breaks!!
# class LongTermMemoryMiddleware(AgentMiddleware[CustomAgentState]):
#     """Middleware that intercepts llm request and injects memory related info to system messages"""
#     state_schema = CustomAgentState

#     def before_model(self, state):
#         print(state)
#         return super().before_model(state)

#     def modify_model_request(self, request: ModelRequest, state: CustomAgentState) -> ModelRequest:
#         print(request.system_prompt)
#         user_id = state.get("user_id")
#         app_name = state.get("app_name")

#         print(f"Middleware is running for user: {user_id} and app: {app_name}")
#         return request

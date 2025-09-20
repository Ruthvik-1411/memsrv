"""A custom implementation for PreLoadMemoryTool() of google-adk but for langchain"""

from langchain_core.messages import SystemMessage

from shared.memory_client import MemoryClient

memory = MemoryClient()

BASE_SYSTEM_INSTRUCTIONS = """You are a helpful agent who can answer user questions about current time
and can do calculations. For any queries that require latest/external information,
identify if any remote agents can help with that. Once you found the relevant agents,
use the appropriate tools to get the answer the user query."""

def preload_memory_prompt(state):
    """Intervenes in an llm request and injects memories into context"""

    system_instructions = BASE_SYSTEM_INSTRUCTIONS
    user_id = state.get("user_id")
    app_name = state.get("app_name")
    raw_user_memories = memory.get_memories(user_id=user_id, app_id=app_name)

    if not raw_user_memories["memories"]:
        system_msg = SystemMessage(system_instructions)
        return [system_msg] + state["messages"]

    memory_text = ""
    for item in raw_user_memories["memories"]:
        memory_text += item["document"] + "\n"

    memory_context = f"""The following content is from your previous conversations with the user.
They may be useful for answering the user's current query.
<PAST_CONVERSATIONS>
{memory_text}
</PAST_CONVERSATIONS>
"""
    system_msg = SystemMessage(system_instructions + memory_context)
    return [system_msg] + state["messages"]

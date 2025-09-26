"""A custom implementation for PreLoadMemoryTool() of google-adk"""
# pylint: disable=protected-access
from typing_extensions import override

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.adk.models.llm_request import LlmRequest

from shared.memory_client import MemoryClient

memory = MemoryClient()

class CustomMemoryTool(BaseTool):
    """Simple implementation of PreLoadMemoryTool() to use memsrv"""
    def __init__(self, name, description):
        super().__init__(name=name, description=description)

    @override
    async def process_llm_request(self, *, tool_context: ToolContext, llm_request: LlmRequest):
        """Intervenes in an llm request and injects memories into context"""
        # Get the details for this user/session/app
        # session_id = tool_context._invocation_context.session.id
        user_id = tool_context._invocation_context.user_id
        app_name = tool_context._invocation_context.app_name
        # agent_name = tool_context._invocation_context.agent.name

        # print(f"Details: {session_id}::{user_id}::{app_name}::{agent_name}")
        user_content = tool_context.user_content
        user_query = user_content.parts[0].text
        print("User query:", user_query)

        # For testing we can hardcode this and comment below logic for fetching from memory client
        # memory_text = "I like watching action movies.\n My name is ruths and I am a student."

        # We fetch memories associated with this user and app from our memory service, memsrv
        # See https://github.com/Ruthvik-1411/memsrv for more details on how the service works
        try:
            raw_user_memories = memory.get_memories(user_id=user_id, app_id=app_name)
        except Exception as e:
            print("Error occured while fetching memories, proceeding without memory.")
            return
        
        if not raw_user_memories["memories"]:
            return
        memory_text = ""
        for item in raw_user_memories["memories"]:
            memory_text += item["document"] + "\n"
        sys_instr = f"""The following content is from your previous conversations with the user.
They may be useful for answering the user's current query.
<PAST_CONVERSATIONS>
{memory_text}
</PAST_CONVERSATIONS>
"""
        llm_request.append_instructions([sys_instr])

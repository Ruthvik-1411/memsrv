from typing_extensions import override

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.adk.models.llm_request import LlmRequest

from adk_agent.memory_client import MemoryClient

memory = MemoryClient()

class CustomMemoryTool(BaseTool):
    def __init__(self, name, description):
        super().__init__(name=name, description=description)
    
    @override
    async def process_llm_request(self, *, tool_context: ToolContext, llm_request: LlmRequest):

        session_id = tool_context._invocation_context.session.id

        user_id = tool_context._invocation_context.user_id

        app_name = tool_context._invocation_context.app_name

        agent_name = tool_context._invocation_context.agent.name
        
        print(f"Details: {session_id}::{user_id}::{app_name}::{agent_name}")
        user_content = tool_context.user_content
        user_query = user_content.parts[0].text
        print("User query:", user_query)
        memory_text = "I like watching action movies.\n My name is ruths and I am a student."
        # FIXME: Hard coding for now, but should get it from tool context
        # raw_user_memories = memory.get_memories(user_id="ruths@gmail.com", app_id="simple_agent")
        # if not raw_user_memories["facts"]:
        #     return
        # memory_text = ""
        # for item in raw_user_memories["facts"]:
        #     memory_text += item["fact"] + "\n"
        updated_instructions = f"""The following content is from your previous conversations with the user.
They may be useful for answering the user's current query.
<PAST_CONVERSATIONS>
{memory_text}
</PAST_CONVERSATIONS>
"""
        llm_request.append_instructions([updated_instructions])
"""Core module for agent orchestration"""
# pylint: disable=protected-access
from typing import List
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from adk_agent.tools import get_current_time, calculate_expression
from adk_agent.custom_memory_tool import CustomMemoryTool

from dotenv import load_dotenv

from shared.memory_client import MemoryClient
# To load the google api keys
load_dotenv()

memory_client = MemoryClient()

def save_memories(memories: List[str], tool_context: ToolContext):
    """Add key memories to the memory service.
    Args:
        memories: list of memory content to be added to the database
    """
    user_id = tool_context._invocation_context.user_id
    app_name = tool_context._invocation_context.app_name
    session_id = tool_context._invocation_context.session.id

    try:
        response = memory_client.create_memory(memory_content=memories,
                                               metadata={
                                                   "user_id": user_id,
                                                   "app_id": app_name,
                                                   "session_id": session_id,
                                                   "agent_name": app_name
                                               })
        print(response)
        return {
            "success": response
        }
    except Exception as e:
        raise ValueError(e) from e

root_agent = Agent(
    name="root_agent",
    model="gemini-2.0-flash",
    description="Agent to answer questions using tools provided.",
    instruction="""You are a helpful agent who can answer user questions about current time
    and can do calculations. For any queries that require latest/external information,
    identify if any remote agents can help with that. Once you found the relevant agents,
    use the appropriate tools to get the answer the user query.""",
    tools=[get_current_time,
           calculate_expression,
           CustomMemoryTool(name="memory_tool", description="preload_memory"),
        #    save_memories
    ]
)

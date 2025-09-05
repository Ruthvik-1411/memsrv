"""Core module for agent orchestration"""
from google.adk.agents import Agent

from adk_agent.tools import get_current_time, calculate_expression
from adk_agent.custom_memory_tool import CustomMemoryTool

from dotenv import load_dotenv
# To load the google api keys
load_dotenv()

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
           CustomMemoryTool(name="memory_tool", description="preload_memory")
    ]
)

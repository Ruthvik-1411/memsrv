"""Core module for agent orchestration"""
import os
from dotenv import load_dotenv

from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI

from tools import get_current_time, calculate_expression

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key)
custom_tools = [get_current_time, calculate_expression]

class CustomAgentState(AgentState):
    user_id: str
    app_name: str

root_agent = create_agent(
    name="root_agent",
    model=llm,
    prompt="""You are a helpful agent who can answer user questions about current time
    and can do calculations. For any queries that require latest/external information,
    identify if any remote agents can help with that. Once you found the relevant agents,
    use the appropriate tools to get the answer the user query.""",
    tools=custom_tools,
    state_schema=CustomAgentState,
    checkpointer=InMemorySaver()
    )

# from langchain_core.messages.base import messages_to_dict
# parsed_msgs = messages_to_dict(first_turn.get("messages"))

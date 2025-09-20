"""Core module for agent orchestration"""
import os
from dotenv import load_dotenv

from langchain.agents import create_agent, AgentState
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_agent.tools import get_current_time, calculate_expression
from langchain_agent.custom_memory_tool import preload_memory_prompt

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
    prompt=preload_memory_prompt, # 1. Dynamic prompt creation for long-term-memory
    tools=custom_tools,
    state_schema=CustomAgentState,
    checkpointer=InMemorySaver()
    )

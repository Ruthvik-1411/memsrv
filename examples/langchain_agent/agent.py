"""Core module for agent orchestration"""
import os
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain.agents.middleware import DynamicSystemPromptMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_agent.tools import get_current_time, calculate_expression
from langchain_agent.custom_memory_tool import (CustomAgentState,
                                                preload_memory_prompt,
                                                preload_memory_prompt_for_middleware)

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=api_key
)
custom_tools = [get_current_time, calculate_expression]

# NOTE: A lot of the implementation can become absolete or break
# as langchain is actively shifting to v1-alpha

# 1. Dynamic prompt creation for long-term-memory
root_agent = create_agent(
    name="root_agent",
    model=llm,
    prompt=preload_memory_prompt,
    tools=custom_tools,
    state_schema=CustomAgentState,
    checkpointer=InMemorySaver() # For example usage we'll use in-memory, modify as needed
    )

# 2. Using Agent middleware
# This was added in langchain 1.0.0a6, these changes are active and can break
# custom_memory_middleware = DynamicSystemPromptMiddleware(preload_memory_prompt_for_middleware)

# root_agent = create_agent(
#     name="root_agent",
#     model=llm,
#     tools=custom_tools,
#     context_schema=CustomAgentState,
#     middleware=[custom_memory_middleware],
#     checkpointer=InMemorySaver() # For example usage we'll use in-memory, modify as needed
#     )

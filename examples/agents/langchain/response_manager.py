"""Module that handles interaction with the agent, maintains session and query passing."""
import uuid
import logging

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import message_to_dict

from .agent import root_agent
from .utils import format_messages_to_events

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

class ResponseManager:
    """Class that handles the respone management with root agent"""
    def __init__(self, user_id: str):
        self.agent = root_agent
        self.user_id = user_id
        self.in_memory_sessions = []

    async def invoke_agent(self, session_id: str, query: str):
        """Invokes the root agent while maintaining sessionid
        for continuance"""
        try:
            logger.info(f"Fetching session data with id: {session_id}")
            if session_id not in self.in_memory_sessions:
                # Ideally we use a db session manager, but this is a simple workaround
                logger.info(f"Session doesn't exist, using new session with id: {session_id}")
                self.in_memory_sessions.append(session_id)

            session: RunnableConfig  = {
                "configurable": {
                    "thread_id": session_id
                }
            }
            logger.info(f"{session_id} Running query: {query}")
            messages = [
                {
                    "role": "user",
                    "content": query
                }
            ]

            final_message = ""
            for event in self.agent.stream(
                input={
                    "user_id": self.user_id,
                    "app_name": self.agent.name,
                    "messages": messages
                },
                # For middleware, we pass in context
                context={
                    "user_id": self.user_id,
                    "app_name": self.agent.name,
                },
                config=session,
                stream_mode="values"
            ):
                latest_message = event["messages"][-1]
                if latest_message.content:
                    if latest_message.type == "human":
                        yield {
                            "is_final_response": False,
                            "status": "sending",
                            "result": latest_message.content,
                            "event": message_to_dict(latest_message)
                        }
                    elif latest_message.type == "ai":
                        final_message = latest_message
                        yield {
                            "is_final_response": False,
                            "status": "finished",
                            "result": latest_message.content,
                            "event": message_to_dict(latest_message)
                        }
                    elif latest_message.type == "tool":
                        yield {
                            "is_final_response": False,
                            "status": "tool_response",
                            "event": message_to_dict(latest_message)
                        }
                elif latest_message.tool_calls:
                    yield {
                        "is_final_response": False,
                        "status": "tool_call",
                        "event": message_to_dict(latest_message)
                    }

            if final_message:
                logger.info("Response generation complete.")
                yield {
                    "is_final_response": True,
                    "status": "finished",
                    "result": final_message.content,
                    "event": message_to_dict(final_message)
                }
        except Exception as e:
            logger.error(f"Error generating response. {str(e)}")
            yield {
                "is_final_response": True,
                "status": "fail",
                "result": "No final response received",
                "error_message": str(e)
            }

    async def dump_session_events(self, session_id: str):
        """Dump session events"""
        graph_state = self.agent.get_state({
            "configurable": {
                "thread_id": session_id
            }
        })
        session_events = format_messages_to_events(graph_state.values.get("messages", []))

        return session_events

async def test_agent():
    """Utils function to test the agent using response manager"""
    response_manager = ResponseManager(user_id="u_123")

    session_id = str(uuid.uuid4())

    first_query = "What's the current time in India?"

    first_response = response_manager.invoke_agent(session_id=session_id, query=first_query)
    async for response in first_response:
        logger.info(f"Events: {response}")

# import asyncio
# asyncio.run(test_agent())

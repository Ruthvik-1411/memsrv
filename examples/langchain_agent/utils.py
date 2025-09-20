"""Common utils for langchain agents"""
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

def format_messages_to_events(messages: list):
    """Formats langchain messages into format acceptable
    by memory backend or openai standard"""
    events = []
    for message in messages:
        if isinstance(message, HumanMessage):
            role = "user"
            parts = [{
                "text": message.content
            }]
        elif isinstance(message, AIMessage):
            role = "model"
            if message.tool_calls:
                parts = [{
                    "function_call": tool_call
                } for tool_call in message.tool_calls]
            else:
                parts = [{
                    "text": message.content
                }]
        elif isinstance(message, ToolMessage):
            role = "user"
            parts = [{
                "function_response": {
                    "id": message.id,
                    "name": message.name,
                    "response": eval(message.content)
                }
            }]
        else:
            print("Unidentified message type, skipping formatting.")

        events.append({
            "parts": parts,
            "role": role
        })
    return events

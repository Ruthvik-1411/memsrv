import json

def parse_conversation(data):
    result = []
    for message in data:
        role = message.get("role")
        for part in message.get("parts", []):
            if "text" in part:
                text = part["text"].strip()
                if role == "user":
                    result.append(f"User: {text}")
                elif role == "model":
                    result.append(f"Model: {text}")
    return "\n".join(result)

events = [
  {
    "parts": [{ "text": "hello" }],
    "role": "user"
  },
  {
    "parts": [{ "text": "Hello! How can I help you today?\n" }],
    "role": "model"
  },
  {
    "parts": [{ "text": "my name is ruths, i like action movies" }],
    "role": "user"
  },
  {
    "parts": [
      {
        "text": "Nice to meet you, Ruths. I like helping people. Do you have any questions for me?\n"
      }
    ],
    "role": "model"
  },
  {
    "parts": [{ "text": "can you tell me what the time is now in india?" }],
    "role": "user"
  },
  {
    "parts": [
      {
        "function_call": {
          "id": "adk-8154f5af-9317-40df-b644-fca873e3e418",
          "args": { "country": "India" },
          "name": "get_current_time"
        }
      }
    ],
    "role": "model"
  },
  {
    "parts": [
      {
        "function_response": {
          "id": "adk-8154f5af-9317-40df-b644-fca873e3e418",
          "name": "get_current_time",
          "response": {
            "status": "success",
            "result": "The current time in India is 2025-08-16 14:44:08 IST+0530"
          }
        }
      }
    ],
    "role": "user"
  },
  {
    "parts": [
      { "text": "The current time in India is 2025-08-16 14:44:08 IST+0530.\n" }
    ],
    "role": "model"
  },
  { "parts": [{ "text": "cool thanks" }], "role": "user" },
  {
    "parts": [
      {
        "text": "You're welcome! Is there anything else I can help you with today?\n"
      }
    ],
    "role": "model"
  }
]

print(parse_conversation(events))
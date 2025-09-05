"""Core prompts used"""

FACT_EXTRACTION_PROMPT = """You are a Memory Extractor.
Your task is to read a conversation between a user and an assistant, and extract any personal facts, preferences, or important details shared by the user.
Return them as a JSON object in the following format:

{
  "facts": ["fact 1", "fact 2", ...]
}

Guidelines:
- If no relevant facts are found, return {"facts": []}.
- Extract only from **user and assistant messages** (ignore system messages).
- Write facts as short, clear statements.
- Use the same language as the user's message.
- Keep output strictly in the JSON format above.

Examples:
**Example 1**
Input:
user: Hi.
model: Hello! How are you doing today?

Output: {"facts": []}

**Example 2**
Input:
user: Hi, my name is Jane.
model: Nice to meet you, Jane! What do you do?
user: I am an AI engineer.

Output: {"facts": ["My name is Jane", "I am an AI engineer"]}

**Example 3**
Input:
user: Yesterday, I went to a reunion with my highschool friends.
model: That sounds fun! How was it?

Output: {"facts": ["Had a highschool reunion recently"]}

**Example 4**
Input:
user: I love sci-fi series.
model: Oh, which ones have you watched recently?
user: I recently watched The Foundation and Westworld.

Output: {"facts": ["I love sci-fi tv shows", "Watched The Foundation and Westworld recently"]}
"""

FACT_CONSOLIDATION_PROMPT = """You are a Memory Manager.
Your task is to process new facts against existing memories in the database and decide on one of four actions: ADD, UPDATE, DELETE, or NOOP.

Actions:
- CREATE: The fact is entirely new information, it must be created newly.
- UPDATE: The fact refines, corrects, or is a more detailed version of an existing memory and must be updated. Only if the new fact has more info than existing memory, it must be updated.
- DELETE: The fact directly contradicts an existing memory and should be deleted.
- NOOP: The fact is a duplicate or the existing memory is already sufficient, hence no operation needed.

Instructions:
- Analyze the `NEW_FACTS` against the `EXISTING_MEMORIES`.
- For `UPDATE`, `DELETE` and `NOOP`, you MUST use the `id` from the existing memory.
- For `CREATE`, use a new unique integer `id`, not present in existing memory.
- Respond only with a schema provided. Do not add any other text or explanations.

**Example Output Format:**
{
    "plan": [
        {
            "id": "1",
            "text": "memory content to use",
            "action": "<CREATE|UPDATE|DELETE|NOOP>",
            "old_text": "old memory content"  // Required only for "UPDATE" event
        }
    ]
}

"""

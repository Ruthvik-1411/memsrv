# Google ADK Agent Integration

The `google-adk` library provides an in-built tool called **`PreloadMemoryTool`**, which preloads memory for a particular user into the session.  
This ensures that when a user interacts with the agent, past relevant information is retrieved and appended to the system instructions, giving the LLM essential context from previous sessions.

## How It Works

1. When a user sends a message:
   - The `PreloadMemoryTool` fetches similar memories for this user message.
   - These memories are **appended** to the system instructions.
   - The LLM now responds with context of key information(facts/memories) from prior sessions.

2. Example implementations:
   - Built-in version: [PreloadMemoryTool()](https://github.com/google/adk-python/blob/main/src/google/adk/tools/preload_memory_tool.py#L29) in adk-python.
   - Custom version (fetching memories via `memsrv`): [examples/agents/adk/custom_memory_tool.py](./custom_memory_tool.py#L38)
      - which uses [examples/shared/memory_client.py](../../shared/memory_client.py) to get memories from memsrv backend.

## Running the Example

First, make sure the **`memsrv`** service is running. Follow the setup instructions [here](../../../README.md#running-the-server).

> Install the required packages to run this example if not done already by running the commands here: [Installing dependencies for examples](../../../docs/Setup.md#example-dependencies)

Then run:

```bash
# Activate your virtual environment
source .venv/bin/activate # or .venv\Scripts\activate on Windows

cd examples

# Create a .env file (refer to env.example in th examples/ folder)
# run the ui file as a module
python -m streamlit run ui\streamlit_adk.py
```

## Next steps

- Try editing `custom_memory_tool.py` to pull memories from different backends such as `VertexAIMemoryBank` or `mem0` etc.
- Explore how ADK automatically manages context injection compared to other frameworks such as langchain/langgraph.
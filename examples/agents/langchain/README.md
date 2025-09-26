# LangChain / LangGraph Agent Integration

For agents built with **LangChain** and **LangGraph**, memory injection into the context is **not standardized** like in Google ADK.  
Instead, you can dynamically modify the system prompt with user memories before the LLM is called.

There are two methods for doing this, as per the latest version of langchain.

## Setup

First, ensure the **`memsrv`** service is running. Follow the setup instructions [here](../../../README.md#running-the-server).

> Install the required packages to run this example if not done already by running the commands here: [Installing dependencies for examples](../../../docs/Setup.md#example-dependencies)

Then run:

```bash
# Activate your virtual environment
source .venv/bin/activate # or .venv\Scripts\activate on Windows

cd examples

# Install the latest pre-release LangChain
uv pip install --pre -U langchain==1.0.0a6

# Create a .env file (refer to env.example in examples/ folder, add LangSmith tracing vars if needed)
# run the ui file as a module
python -m streamlit run ui\streamlit_langchain.py
```

## Method 1: Using a Callable Prompt (Stable)

A simple approach where you pass a function as the system prompt when creating the agent.
That function (`preload_memory_prompt`) fetches memories and dynamically constructs the system prompt.

Code: [examples/agents/langchain/agent.py](agent.py#L28) and [examples/agents/langchain/custom_memory_tool.py](custom_memory_tool.py#L18)

```python
# In agent.py
root_agent = create_agent(
    ...
    prompt=preload_memory_prompt, # prompt is a callable here
    state_schema=CustomAgentState,
    ...
)
```

## Method 2: Using Agent Middleware (Advanced)

A more flexible approach using **AgentMiddleware**.
Here, `DynamicSystemPromptMiddleware` intercepts the request before it's sent to the model, fetches memories via
`preload_memory_prompt_for_middleware`, and injects the updated system prompt statelessly.

Code: [examples/agents/langchain/agent.py](agent.py#L38) and [examples/agents/langchain/custom_memory_tool.py](custom_memory_tool.py#52)

```python
# In agent.py
custom_memory_middleware = DynamicSystemPromptMiddleware(
    preload_memory_prompt_for_middleware
)

root_agent = create_agent(
    ...
    middleware=[custom_memory_middleware],
    context_schema=CustomAgentState,
    ...
)
```

## Choosing Between the Two

- **Callable Prompt (Method 1)**:
    - Simpler and relies on stable APIs.
    - Recommended for production.

- **Agent Middleware (Method 2)**:
    - More flexible, but AgentMiddleware is newer and may change in future LangChain versions.
    - Use if you need finer-grained control.

## Next steps

- Experiment with both approaches and compare the outputs to decide what works for you.
- Extend `custom_memory_tool.py` to integrate with any other memory services like Mem0 etc.
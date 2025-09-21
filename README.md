# memsrv

A simple, self-hosted memory service boilerplate for LLMs and agent frameworks.

## Overview

`memsrv` provides a streamlined solution for managing long term memory for your LLM and agentic applications. It allows you to extract, store, and retrieve factual information from conversations, leveraging vector embeddings for semantic search. The service is designed to be modular and extensible, supporting multiple vector database backends and LLM, Embedding providers.

Key features:

*   **Fact Extraction:** Automatically extracts key facts from conversation histories.
*   **Semantic Search:** Uses vector embeddings to enable semantic retrieval of memories based on similarity to a query.
*   **Metadata Filtering:** Supports filtering memories based on metadata such as user ID, session ID, and application ID.
*   **Multiple Database Support:** Pluggable architecture supports different vector databases, such as ChromaDB and Postgres with pgvector.
*   **REST API:** Exposes core memory services through a REST API for easy integration with other applications.
    - The services can be wrapped around functions and can be used as tools with your agent(`memory_as_a_tool`).
*   **CRUD Operations:** Supports Create, Read, Update, and Delete operations over the vector database for memory management.

> Note: This project is still in active development. For status, milestones and next steps of this project refer [Project Milestones](./Milestones.md).

## High level architecture and Flow
<img src="assets/memsrv_arch.png">

## Getting Started

### Prerequisites

*   Python 3.12+
*   uv for dependency management ([uv docs](https://pypi.org/project/uv/))
*   LLM Provider API key for generating content and embeddings.
    - Gemini has a pretty generous limits on their free tier.

### Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/Ruthvik-1411/memsrv.git
    cd memsrv
    ```

2.  Install dependencies using uv:

    ```bash
    # If you don't have uv installed
    pip install uv

    # Create a venv using uv
    uv venv

    # Activate your venv
    source venv/bin/activate or venv\Scripts\activate

    # Install the packages
    uv sync
    ```

3.  Set up your environment variables:

    *   Create a `.env` file in the src folder. Refer [`src/env.example`](src/env.example) for more info.
    *   Add your Google/LLM API key(support for more providers is in progress):
        ```bash
        GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
        ```

    *   If using Postgres, configure the database connection(make sure your postgres connection is active):
        ```bash
        DATABASE_USER=your_db_user
        DATABASE_PASSWORD=your_db_password
        DATABASE_NAME=your_db_name
        DATABASE_HOST=your_db_host (default: 127.0.0.1)
        DATABASE_PORT=your_db_port (default: 5432)
        # Make sure the database with the name exists already
        ```

### Running the Server

To start the API server, use the following command:
```bash
cd src

python server.py
# or
uv run server.py
```
This will start the server at `http://0.0.0.0:8090`.

### Interacting with the API

The API documentation is available at `http://0.0.0.0:8090/api/v1/docs` after the server is running. You can use this documentation to explore the available endpoints and test them out.

## Core Functionality

The `memsrv` service exposes the following core functionalities through its API:

*   **Generating Memories:**  Extracts facts/memories from conversations and stores them in the database, along with metadata and vector embeddings (`/api/v1/memories/generate`).
*   **Creating Memories:**  Directly adds facts/memories and stores them in the database (`/api/v1/memories/create`).
*   **Retrieving Memories by Metadata:** Retrieves memories based on metadata filters such as user ID, session ID, and application ID (`/api/v1/memories`).
*   **Retrieving Memories by Semantic Similarity:** Retrieves memories that are semantically similar to a given query, optionally filtered by metadata (`/api/v1/memories/similar`).
*   **Updating Memories:** Updates existing memories with new content and/or metadata (`/api/v1/memories/update`).
*   **Deleting Memories:** Deletes memories from the database by their IDs (`/api/v1/memories/delete`).

## Configuration

The service's behavior is configured through environment variables and the [`src/config.py`](src/config.py) file. Refer the [`src/env.example`](src/env.example) for the complete list of expected values. Key configuration options include:

*   `LLM_PROVIDER` and `LLM_MODEL`: Specifies the LLM provider and model to use.
*   `DB_PROVIDER`: Specifies the database backend to use (default: `chroma`, options: `chroma`, `postgres`). More are in development.
*   `EMBEDDING_PROVIDER` and `EMBEDDING_MODEL`: Specifies the embedding provider and model to use.
*   Database connection details (if using Postgres) and some other config like API keys.

## Using the service in your agent

> The package installations for running examples is seperated from the core service dependencies. See [Installing dependencies for examples](./Setup.md#example-dependencies) to install the packages for the examples you want to run.

### Google ADK

The `google-adk` library has an in built tool called `PreloadMemoryTool` which preloads memory for a particular user into the session. This is automatically called when a request is sent to LLM. When a user sends a message to the agent, the `PreloadMemoryTool` fetches the similar memories to this user query and **appends** the retrieved memories to the system instructions. That way the when the LLM starts responding, it will have the key information from previous sessions.

In the [examples/adk_agent/custom_memory_tool.py](examples/adk_agent/custom_memory_tool.py) you can find the same implementation, but we fetch memories from our client which communicates with our memory service running on `http://localhost:8090`. See [examples/shared/memory_client.py](examples/shared/memory_client.py) for more info.

To get started, make sure the `memsrv` service is running, follow the steps [here](#running-the-server).
```bash
# In a new terminal
# Activate your venv
source venv/bin/activate or venv\Scripts\activate

cd examples

# create a .env file. refer env.example in that folder
streamlit run app.py
```

Open the streamlit app running at `http://localhost:8501/`. Choose the user id to test and do some conversation, possibly saying some facts about you, name, likes etc. Once done, click on new session. We add memories after a session is completed, hence, when you now say hi or hello, the agent should be using the information from your previous session.

### LangChain/LangGraph
For agents built with LangChain and LangGraph, the process of injecting memory into the context is not standardized in the same way as google-adk. It requires a more custom approach. There are essentially two primary methods to dynamically modify the system prompt with user memories before the LLM is called.
The implementation can be found in [examples/langchain_agent](examples/langchain_agent/). To run the example, first ensure the memsrv is running, then execute the following:
> PATCH: Since we are using the latest langchain lib, install the latest version using, <br>`uv pip install --pre -U langchain==1.0.0a6`
```bash
# Activate your venv
source venv/bin/activate # or venv\Scripts\activate

cd examples

# create a .env file. refer env.example in that folder (add langsmith tracing vars if needed)
streamlit run app_langchain.py
```
#### Method 1: Using a Callable Prompt

This is a straightforward and stable method where we pass a function directly as the prompt when creating the agent.
This function, `preload_memory_prompt`, uses the agent's current state (containing the user_id/app_id) to fetch memories and construct a new system prompt dynamically. The complete logic can be found in [examples/langchain_agent/custom_memory_tool.py](examples/langchain_agent/custom_memory_tool.py).
```python
# In langchain_agent/agent.py
root_agent = create_agent(
    ...
    prompt=preload_memory_prompt, # The prompt is a callable/function
    state_schema=CustomAgentState,
    ...
)
```
#### Method 2: Using Agent Middleware

This is a more advanced approach using `AgentMiddleware` to statelessly intercept the request just before it's sent to the model.
We use `DynamicSystemPromptMiddleware` which takes a function, `preload_memory_prompt_for_middleware`. This function accesses runtime context (like user_id/app_id) to fetch memories and returns the new prompt string, which the middleware then injects into the model request. The implementation details are in [examples/langchain_agent/agent.py](examples/langchain_agent/agent.py) and [examples/langchain_agent/custom_memory_tool.py](examples/langchain_agent/custom_memory_tool.py).
```python
# In langchain_agent/agent.py
custom_memory_middleware = DynamicSystemPromptMiddleware(preload_memory_prompt_for_middleware)

root_agent = create_agent(
    ...
    middleware=[custom_memory_middleware],
    context_schema=AgentContext,
    ...
)
```
You can playaround with both methods and see what works best.
>**A Note on Stability**: LangChain and LangGraph are under rapid development. The Agent Middleware API is a newer feature and may change in future versions, which could break the implementation of Method 2. Method 1 (Callable Prompt) relies on a more core, stable feature.

## Directory Structure

```
└── memsrv/
    ├── README.md                       # This file
    └── src/
        ├── config.py                   # Configuration file for selecting LLMs and vector DBs
        ├── server.py                   # Entry point for running the FastAPI server
        └── memsrv/
            ├── api/
            │   ├── main.py             # FastAPI application entry point
            │   └── routes/
            │       └── memory.py       # API routes for memory management
            ├── core/
            │   ├── extractor.py        # Extracts facts from conversations
            │   ├── memory_service.py   # Core logic for memory management
            │   └── prompts.py          # Prompts used for fact extraction
            ├── db/
            │   ├── base_adapter.py     # Abstract base class for database adapters
            │   └── adapters/
            │       ├── __init__.py
            │       ├── chroma.py       # ChromaDB adapter
            │       └── postgres.py     # Postgres adapter
            ├── embeddings/
            │   ├── base_embedder.py    # Abstract base class for embedding providers
            │   └── providers/
            │       └── gemini.py       # Gemini embedding provider
            ├── llms/
            │   ├── __init__.py
            │   ├── base_config.py      # Base class for LLM configurations
            │   ├── base_llm.py         # Abstract base class for LLMs
            │   └── providers/
            │       └── gemini.py       # Gemini LLM provider
            ├── models/
            │   └── memory.py           # Data models for memories
            │   └── requests.py         # Data models for API requests
            │   └── response.py         # Data models for API responses
            └── utils/
                ├── factory.py          # Factory that constructs the individual services(llm, embd, db)
                └── logger.py           # Common logger for all files

```

## License

This project is licensed under MIT License, see [LICENSE](./LICENSE) file for more info. Feel free to modify and use as needed and build on top of this.

# Memsrv

**Memsrv** is a lightweight, self-hosted memory service for LLMs and agent frameworks. It helps your Agentic or LLM applications **remember facts across sessions**, retrieve information with **semantic search**, and plug into your existing agents with minimal setup. Think of it as a **memory layer** that makes your models more context-aware, consistent and personalized over time.

## Overview

`Memsrv` is built to give LLMs and agent frameworks a reliable way to manage long-term memory. Instead of relying on session context alone, it provides a structured service for:
* **Fact Extraction** - distilling key information from conversations into structured "memories".
* **Vector based Storage** - encoding facts as embeddings for semantic search.
* **Metadata Filtering** - retrieving memories tied to a specific user, session, or application.

The service is:
* **Modular** - supports multiple vector database backends (e.g., ChromaDB, Postgres with pgvector).
* **Extensible** - works with different LLM and embedding providers.
* **Integrable** - exposes a REST API so memories can be queried or updated from any application, or wrapped directly as tools within your agents.

This design is inspired by [VertexAI Memory Bank](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/memory-bank/overview), but implemented in a lightweight, self-hosted way for developers who want full control over their agent’s memory layer.

> Note: This project is still in active development. For status, milestones and next steps of this project refer [Project Milestones](docs/Milestones.md#project-milestones).

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
This will start the server at `http://localhost:8090`.

### Interacting with the API

The API documentation is available at `http://localhost:8090/api/v1/docs` after the server is running. You can use this documentation to explore the available endpoints and test them out.

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

> The package installations for running examples is seperated from the core service dependencies. See [Installing dependencies for examples](docs/Setup.md#example-dependencies) to install the packages for the examples you want to run.

### Google ADK
See [examples/agents/adk/README.md](examples/agents/adk/README.md) for details on how to use `google-adk` with memory injection and the `PreloadMemoryTool`.

### LangChain / LangGraph
See [examples/agents/langchain/README.md](examples/agents/langchain/README.md) for details on integrating memory into agents built with LangChain or LangGraph, including both the **Callable Prompt** and **Agent Middleware** approaches.

## Directory Structure

```
└── memsrv/
    ├── README.md                       # This file
    └── src/
        ├── config.py                   # Configuration file for selecting LLMs and vector DBs and respective config vars
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
            │   ├── utils.py            # Utils file for common funcs for db
            │   └── adapters/
            │       ├── __init__.py
            │       ├── chroma_lite.py  # ChromaDBLite adapter (local)
            │       ├── chroma.py       # ChromaDB adapter (client-server)
            │       └── postgres.py     # Postgres adapter
            ├── embeddings/
            │   ├── base_config.py      # Base class for embedding configurations
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

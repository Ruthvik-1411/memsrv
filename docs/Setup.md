# Guide to setup environment, run examples and further dev

## Setting Up and Dependency Management with UV

This project uses uv for dependency management and reproducible environments. Because the repository has two different usage modes, the core memory service and the examples. So we need to manage dependencies in a structured way, for the core service and examples.

### 1. Why are we doing this?

The core service `memsrv` should stay lightweight and clean, containing only what's needed to run the memory service and the pluggable providers (LLMs, embeddings, vector databases).

The examples (`examples/`) often need heavy external frameworks like langchain, google-adk and more. These are optional and not everyone running the core service needs them.

By separating dependencies:
  - We avoid bloating the core install with unnecessary packages.
  - Devs/Users can choose exactly what they need.
  - The project stays easier to maintain and extend.

### 2. Why is this needed?
Without separation, the environment would include all possible dependencies, FastAPI/MCP + DB drivers + ADK + Langchain + more.

This leads to:
- Slower installs and larger containers.
- A higher chance of dependency conflicts.
- Confusion for devs/users who just want the core service.

By organizing dependencies into core and optional groups, we keep the project modular and flexible.

### 3. How are we doing it?

We use <a href="https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-groups">uv's dependency groups</a> feature.

#### Core dependencies
Core packages are declared under `[project]` in pyproject.toml.
These cover the dependencies for core service, providers (LLMs, embeddings, Vector DBs), and common utilities.
Example:
```bash
uv add fastapi uvicorn pydantic
uv add chromadb asyncpg google-genai
```

Install core dependencies:
```bash
uv sync
```

#### Example dependencies

Optional integrations (e.g., LangChain, ADK) live in `[dependency-groups]`.

Adding a dependency to a group:
```bash
uv add --group examples-langchain langchain
uv add --group examples-adk google-adk
```

Installing for examples:
```bash
# Install ADK example deps
uv sync --group examples-adk

# Install only LangChain example deps
uv sync --group examples-langchain

# Install all optional deps
uv sync --group examples-all
```

## Additional help
<details>
<summary>Generating requirements.txt</summary>
If you need a requirements.txt file to use with your own dep manager or for dockerizing you can get them by running the following commands.

Commands to run:

```bash
# For complete list of packages
uv pip freeze > requirements.txt

# For a more detailed version with dependency info
uv pip compile pyproject.toml -o requirements.txt
```
</details>

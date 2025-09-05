"""Docker file to run the service.(Note: Yet to test this!)"
# Use official uv + Python image
# Lighter image
FROM ghcr.io/astral-sh/uv:python3.12-alpine
# More libs, slower and heavy
# FROM ghcr.io/astral-sh/uv:python3.12-bookworm

# Set working directory
WORKDIR /app

# Set env vars
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (creates .venv)
RUN uv sync --locked

# Copy the rest of the source code
COPY src/ ./src

# Expose port (optional: match server.py default)
EXPOSE 8090

# Run your server from the src dir
CMD ["python", "src/server.py", "--host=0.0.0.0", "--port=8090"]

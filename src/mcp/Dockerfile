FROM python:3.12-slim-bullseye

USER root
WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv
COPY pyproject.toml main.py ./

RUN uv venv /app/.venv \
    && uv run main.py

ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV EPR_URL=http://localhost:8042
ENV EPR_DEBUG=false

# Expose the port your MCP server listens on
EXPOSE 8000


# Command to run your MCP server application
CMD ["/app/.venv/bin/python3", "-m", "main"]
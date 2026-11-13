FROM python:3.12-slim-bullseye

USER root
WORKDIR /app

COPY pyproject.toml main.py ./

# Install uv, then use it to install the project dependencies system-wide.
RUN pip install --no-cache-dir uv && \
    uv pip install --system fastmcp httpx2

ENV EPR_URL=http://host.docker.internal:8042
ENV EPR_DEBUG=false

# The MCP server speaks stdio: start the container with docker run -i ...
CMD ["python", "main.py"]

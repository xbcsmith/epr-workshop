# EPR MCP Server

## Workshop: Building an MCP Server with Python and FastMCP

In this workshop, you will learn how to build a simple MCP server using Python
and FastMCP 4. We will walk through the structure and logic of a real-world MCP
server.

---

## Setup

Create a work directory and initialize a project with `uv`:

```bash
mkdir work
cd work
uv init
uv add fastmcp httpx2
```

---

## Understanding the Server Structure

Your MCP server will:

- Register tools (API endpoints) for interacting with an Event Provenance
  Registry (EPR)
- Use async HTTP requests to communicate with the EPR backend
- Provide logging support

---

## Create a Basic MCP Server

```bash
touch main.py
```

### Imports

```python
import logging
import os
import sys

import httpx2
from fastmcp import FastMCP
```

---

### Logging

The MCP stdio transport uses stdout to carry the MCP protocol. All logging must
go to stderr to avoid corrupting the protocol stream.

```python
debug = bool(os.environ.get("EPR_DEBUG", False))
level = logging.DEBUG if debug else logging.INFO
log_format = "%(asctime)s %(name)s:[%(levelname)s] %(message)s"
logging.basicConfig(stream=sys.stderr, level=level, format=log_format)
logger = logging.getLogger(__name__)
```

---

### Configuration

Create the FastMCP server instance. The second positional argument to `FastMCP`
is `instructions`, not `version`, so always pass `version` by keyword to avoid
confusion:

```python
mcp = FastMCP(name="EPR Workshop MCP Server", version="0.1.0")

epr_url = os.environ.get("EPR_URL", "http://localhost:8042")
epr_token = os.environ.get("EPR_TOKEN", "")
```

---

### Register Tools (Endpoints)

Each tool is an async function decorated with `@mcp.tool`. For example, to fetch
an event:

```python
@mcp.tool(title="Fetch Event", description="Fetch an event from EPR")
async def fetch_event(id: str) -> str:
    """Fetch an event from the EPR by its ID."""
    async with httpx2.AsyncClient() as client:
        response = await client.get(f"{epr_url}/api/v1/events/{id}")
        return response.text
```

You can register as many tools as needed, such as:

- Fetching events, receivers, and groups
- Searching with GraphQL queries
- Creating new events, receivers, and groups

Each tool should handle HTTP requests and return results or error messages.

---

### Run the MCP Server

Always guard `mcp.run()` inside `if __name__ == "__main__":` to prevent the
server from starting at import time. Pass `show_banner=False` to suppress the
FastMCP startup banner, which would corrupt the stdio protocol stream if printed
to stdout:

```python
if __name__ == "__main__":
    logger.info("MCP is running: url=%s token_set=%s", epr_url, bool(epr_token))
    mcp.run(show_banner=False)
```

---

## Build the Server

### Create a Project Config

Create the `pyproject.toml`:

```bash
touch pyproject.toml
```

Add the following:

```toml
[build-system]
requires = ["setuptools>=40.8.0", "wheel"]
build-backend = "setuptools.build_meta:__legacy__"

[project]
name = "epr-mcp-server"
version = "0.1.0"
description = "MCP server for EPR workshop"
requires-python = ">= 3.12"
dependencies = [
    "fastmcp>=4.0,<5",
    "httpx2>=2.13",
]
```

---

### Create Dockerfile

Create a `Dockerfile`:

```bash
touch Dockerfile
```

Add the following content:

```dockerfile
FROM python:3.12-slim-bullseye

USER root
WORKDIR /app

COPY pyproject.toml main.py ./

RUN pip install --no-cache-dir uv && \
    uv pip install --system fastmcp httpx2

ENV EPR_URL=http://host.docker.internal:8042
ENV EPR_DEBUG=false

# The MCP server speaks stdio: start with docker run -i ...
CMD ["python", "main.py"]
```

---

### Build Docker Image

```bash
docker build -t epr-mcp-server:latest .
```

---

## Summary

- Use FastMCP to quickly build async, tool-driven servers in Python.
- Register tools as async functions for each API endpoint.
- Use `httpx2` for async HTTP requests.
- Leverage logging for robust development.

---

## Links

- [FastMCP documentation](https://gofastmcp.com)
- [EPR-MCP-Python](https://github.com/xbcsmith/epr-mcp-python)
- [FastMCP 4 changelog](https://gofastmcp.com/getting-started/whats-new)

---

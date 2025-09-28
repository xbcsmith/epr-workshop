# EPR MCP Server

## Workshop: Building an MCP Server with Python and FastMCP

In this workshop, you'll learn how to build a simple MCP (Multi-Channel
Processor) server using Python and FastMCP 1.0 in the MCP
[python-sdk](https://github.com/modelcontextprotocol/python-sdk) framework.
We'll walk through the structure and logic of a real-world MCP Server.

## Setup

Create a work directory

```bash
mkdir ./src
cd ./src
```

Create and activate a virtual environment:

```bash
python3 -m venv ./venv/epr-mcp-server
source ./venv/epr-mcp-server/bin/activate
```

Install the required dependencies:

```bash
pip install mcp[cli] mcp httpx
```

---

## Understanding the Server Structure

Your MCP server will:

- Register tools (API endpoints) for interacting with an Event Provenance
  Registry (EPR)
- Use async HTTP requests to communicate with the EPR backend
- Provide logging and debugging support

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

import httpx
from mcp.server.fastmcp import FastMCP
```

---

### Debugging and Logging

Set up debugging and logging based on configuration or environment variables:

```python
def debug_except_hook(type, value, tb):
    print(f"epr python hates {type.__name__}")
    print(str(type))
    import pdb
    import traceback
    traceback.print_exception(type, value, tb)
    pdb.post_mortem(tb)


debug = os.environ.get("EPR_DEBUG", False)
level = logging.INFO
if debug:
    sys.excepthook = debug_except_hook
    level = logging.DEBUG
log_format = "%(asctime)s %(name)s:[%(levelname)s] %(message)s"
logging.basicConfig(stream=sys.stderr, level=level, format=log_format)
logger = logging.getLogger(__name__)
```

---

### Add ENV Vars

```bash
epr_url = os.environ.get("EPR_URL", "http://localhost:8042")
epr_token = os.environ.get("EPR_TOKEN", "<N/A>")
```

### Initialize FastMCP

Create an instance of FastMCP, giving your server a name:

```python
mcp = FastMCP("EPR Workshop MCP Server", "0.1.0")
```

---

### Register Tools (Endpoints)

Each tool is an async function decorated with `@mcp.tool`. For example, to fetch
an event:

```python
@mcp.tool(title="Fetch Event", description="Fetch an event from EPR")
async def fetch_event(id: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8042/api/v1/events/{id}")
        return response.text
```

You can register as many tools as needed, such as:

- Fetching events, receivers, and groups
- Searching with GraphQL queries
- Creating new events, receivers, and groups

Each tool should handle HTTP requests and return results or error messages.

---

### Run the MCP Server

Finally, start the server and log the configuration:

```python
logger.info("MCP is running with the following configuration:")
logger.info(f"URL: {epr_url}")
logger.info(f"Token: {epr_token}")
mcp.run()
```

---

## Build the Server

### Create a project config

Create the pyproject.toml

```bash
touch pyproject.toml
```

Add the following:

```python
[build-system]
requires = ["setuptools>=40.8.0", "wheel"]
build-backend = "setuptools.build_meta:__legacy__"

[project]
name = "epr-mcp-server"
version = "0.1.0"
description = "MCP server for EPR workshop"
requires-python = ">= 3.12"
dependencies = [
    "httpx",
    "mcp",
]
```

---

### Create Dockerfile

Create a Dockerfile

```bash
touch Dockerfile
```

Add the following content to the Dockerfile:

```bash
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
ENV EPR_URL=http://localhost:8024
ENV EPR_DEBUG=false

# Expose the port your MCP server listens on
EXPOSE 8000


# Command to run your MCP server application
CMD ["/app/.venv/bin/python3", "-m", "main"]
```

---

### Build docker image

```bash
docker build -t epr-mcp-server:latest .
```

---

## Summary

- Use FastMCP to quickly build async, tool-driven servers in Python.
- Register tools as async functions for each API endpoint.
- Use `httpx` for async HTTP requests.
- Leverage logging and debugging for robust development.

---

## Links

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [EPR-MCP-Python](https://github.com/xbcsmith/epr-mcp-python)
- [FastMCP 2.0](https://gofastmcp.com/getting-started/welcome)

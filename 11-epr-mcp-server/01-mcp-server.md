# EPR MCP Server

## Workshop: Building an MCP Server with Python and FastMCP

In this workshop, you'll learn how to build a simple MCP (Multi-Channel Processor) server using Python and the [FastMCP](https://github.com/xbcsmith/fastmcp) framework. We'll walk through the structure and logic of a real-world `run` function from `server.py` to illustrate best practices.

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv epr-mcp-server
source epr-mcp-server/bin/activate
```

Install the required dependencies:

```bash
pip install mcp[cli] mcp httpx
```

## Project Setup

First, ensure you have the required dependencies:

```bash
pip install mcp[cli] mcp httpx
```

---

## Understanding the Server Structure

Your MCP server will:

- Register tools (API endpoints) for interacting with an Event Provenance Registry (EPR)
- Use async HTTP requests to communicate with the EPR backend
- Provide logging and debugging support

---

## The `run` Function: Core of the Server

The `run(cfg)` function is the entry point for your MCP server. Here’s how it works:

### Debugging and Logging

Set up debugging and logging based on configuration or environment variables:

```python
debug = cfg.debug or os.environ.get("EPR_DEBUG", False)
if debug:
    sys.excepthook = debug_except_hook
    logger.setLevel(logging.DEBUG)
```

### Initialize FastMCP

Create an instance of FastMCP, giving your server a name:

```python
mcp = FastMCP("epr-mcp")
```

### Register Tools (Endpoints)

Each tool is an async function decorated with `@mcp.tool`. For example, to fetch an event:

```python
@mcp.tool(title="Fetch Event", description="Fetch an event from EPR")
async def fetch_event(epr_url: str, id: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{epr_url}/api/v1/events/{id}")
        return response.text
```

You can register as many tools as needed, such as:

- Fetching events, receivers, and groups
- Searching with GraphQL queries
- Creating new events, receivers, and groups

Each tool should handle HTTP requests and return results or error messages.

### Run the MCP Server

Finally, start the server and log the configuration:

```python
logger.info("MCP is running with the following configuration:")
logger.info(f"URL: {cfg.url}")
logger.info(f"Token: {cfg.token}")
mcp.run()
```

---

## Extending Your Server

- Add more tools for additional API endpoints.
- Implement authentication or custom error handling as needed.
- Use the `get_search_query` helper to build flexible search queries.

---

## Example: Registering a Tool

Here’s a minimal example of registering a tool:

```python
@mcp.tool(title="Create Event", description="Create a new event in EPR")
async def create_event(epr_url: str, event_data: dict) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{epr_url}/api/v1/events", json=event_data)
        if response.status_code == 201:
            return "Event created successfully"
        else:
            return f"Failed to create event: {response.text}"
```

---

## Running the Server

Call the `run(cfg)` function with your configuration object to start the MCP server.

---

## Summary

- Use FastMCP to quickly build async, tool-driven servers in Python.
- Register tools as async functions for each API endpoint.
- Use `httpx` for async HTTP requests.
- Leverage logging and debugging for robust development.

---

**Now try adding your own tools and experiment with the endpoints!**

## Links

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [EPR-MCP-Python](https://github.com/xbcsmith/epr-mcp-python)

---


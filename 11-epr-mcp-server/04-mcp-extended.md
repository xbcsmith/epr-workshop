# EPR MCP Server Extended

## Overview

In this section we will extend our MCP server capabilities.

## Extending Your Server

- Add more tools for additional API endpoints.
- Implement authentication or custom error handling as needed.
- Use the `get_search_query` helper to build flexible search queries.

---

## Example: Registering a Tool

Here’s a minimal example of registering a tool:

```python
@mcp.tool(title="Fetch Event", description="Fetch an event from EPR")
async def fetch_event(epr_url: str, id: str) -> str:
    """Fetch an event from the EPR"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{epr_url}/api/v1/events/{id}")
        return response.text
```

---

## Running the Server

Call the `run(cfg)` function with your configuration object to start the MCP server.

---

## Expanding the server

Add two more fetch tools.

```bash
@mcp.tool(title="Fetch Event Receiver", description="Fetch an event receiver from EPR")
async def fetch_receiver(epr_url: str, id: str) -> str:
    """Fetch an event receiver from the EPR"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{epr_url}/api/v1/receivers/{id}")
        return response.text

@mcp.tool(title="Fetch Event Receiver Group", description="Fetch an event receiver group from EPR")
async def fetch_group(epr_url: str, id: str) -> str:
    """Fetch an event receiver group from the EPR"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{epr_url}/api/v1/groups/{id}")
        return response.text
```

## Leverage the GraphQL endpoint

```bash
@mcp.tool(title="Search Events", description="Search for events in EPR")
async def search_events(epr_url: str, data: dict) -> str:
    """Search for events in the EPR"""
    fields = [
        "id",
        "name",
        "version",
        "release",
        "platform_id",
        "package",
        "description",
        "success",
        "event_receiver_id",
    ]
    query = get_search_query(operation="events", params=data, fields=fields)
    async with httpx.AsyncClient() as client:
        headers = {"Content-Type": "application/json"}
        response = await client.post(f"{epr_url}/api/v1/graphql/query", json=query.as_dict_query(), headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            return f"Failed to search events: {response.text}"

@mcp.tool(title="Search Event Receivers", description="Search for event receivers in EPR")
async def search_receivers(epr_url: str, data: dict) -> str:
    """Search for event receivers in the EPR"""
    fields = ["id", "name", "type", "version", "description"]
    query = get_search_query(operation="event_receivers", params=data, fields=fields)
    async with httpx.AsyncClient() as client:
        headers = {"Content-Type": "application/json"}
        response = await client.post(f"{epr_url}/api/v1/graphql/query", json=query.as_dict_query(), headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            return f"Failed to search event receivers: {response.text}"

@mcp.tool(title="Search Event Receiver Groups", description="Search for event receiver groups in EPR")
async def search_groups(epr_url: str, data: dict) -> str:
    """Search for event receiver groups in the EPR"""
    fields = ["id", "name", "type", "version", "description"]
    query = get_search_query(operation="event_receiver_groups", params=data, fields=fields)
    async with httpx.AsyncClient() as client:
        headers = {"Content-Type": "application/json"}
        response = await client.post(f"{epr_url}/api/v1/graphql/query", json=query.as_dict_query(), headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            return f"Failed to search event receiver groups: {response.text}"
```

## Add Danger

```bash
@mcp.tool(title="Create Event", description="Create a new event in EPR")
async def create_event(epr_url: str, event_data: dict) -> str:
    """Create a new event in the EPR"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{epr_url}/api/v1/events", json=event_data)
        if response.status_code == 201:
            return "Event created successfully"
        else:
            return f"Failed to create event: {response.text}"

@mcp.tool(title="Create Event Receiver", description="Create a new event receiver in EPR")
async def create_receiver(epr_url: str, receiver_data: dict) -> str:
    """Create a new event receiver in the EPR"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{epr_url}/api/v1/receivers", json=receiver_data)
        if response.status_code == 201:
            return "Event receiver created successfully"
        else:
            return f"Failed to create event receiver: {response.text}"

@mcp.tool(title="Create Event Receiver Group", description="Create a new event receiver group in EPR")
async def create_group(epr_url: str, group_data: dict) -> str:
    """Create a new event receiver group in the EPR"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{epr_url}/api/v1/groups", json=group_data)
        if response.status_code == 201:
            return "Event receiver group created successfully"
        else:
            return f"Failed to create event receiver group: {response.text}"
```

## Re-Build the docker image

```bash
docker build -t epr-mcp-server:latest .
```

## Restart MCP Server

Restart your MCP server in MCP Inspector or VSCode to see results.


## Summary

- Extend tools

## Misc

Random info that could be helpful

## Alternative UV

UV - An extremely fast Python package and project manager, written in Rust.

[Docs](https://docs.astral.sh/uv)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
export UV_INDEX_URL=$PIP_INDEX_URL
```

```bash
cd src/
uv venv
source .venv/bin/activate
uv add "mcp[cli]" mcp httpx
```

## Altenative Run Commands

To run the MCP server, use the following command:

```bash 
docker run -i --rm --network=host -e EPR_URL -e EPR_TOKEN epr-mcp-server:latest
```

```bash
mcp dev main.py
```

```bash
uv run --with mcp --with mcp[cli] --with pydantic --with httpx mcp run main.py
```
# EPR MCP Server Extended

## Overview

In this section we will extend the Model Context Protocol (MCP) server
capabilities for EPR integration. The extensions add comprehensive CRUD
operations and search functionality for all EPR resource types.

---

### Core Extensions

Fetch Operations: Adds two new fetch tools for retrieving Event Receivers and
Event Receiver Groups by ID using REST API endpoints. These complement the
existing event fetching capability.

GraphQL Search Integration: Implements three search functions that leverage
EPR's GraphQL endpoint to query events, event receivers, and event receiver
groups. Each search function uses the get_search_query helper to build flexible
queries with configurable fields and parameters.

Create Operations: Introduces "danger zone" functionality with three creation
tools that can add new events, event receivers, and event receiver groups to
EPR. These operations modify EPR state and require appropriate caution in usage.

---

### Technical Implementation

The extensions follow consistent patterns using httpx for HTTP requests and
proper error handling. Search operations use GraphQL queries with predefined
field sets, while creation operations use REST POST endpoints with JSON
payloads. All functions are properly decorated as MCP tools with descriptive
titles and documentation.

### Deployment and Alternatives

The document includes Docker rebuild instructions and server restart procedures
to apply the extensions. An alternative implementation section covers using UV
(a Rust-based Python package manager) instead of traditional pip/venv workflows,
along with various command options for running the MCP server locally or in
containers.

The extensions transform the basic MCP server into a comprehensive EPR
management interface that supports both read and write operations across all EPR
resource types.

---

## Expanding the server

Add two more fetch tools.

```bash
@mcp.tool(title="Fetch Event Receiver", description="Fetch an event receiver from EPR")
async def fetch_receiver(id: str) -> str:
    """Fetch an event receiver from the EPR"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{epr_url}/api/v1/receivers/{id}")
        return response.text

@mcp.tool(title="Fetch Event Receiver Group", description="Fetch an event receiver group from EPR")
async def fetch_group(id: str) -> str:
    """Fetch an event receiver group from the EPR"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{epr_url}/api/v1/groups/{id}")
        return response.text
```

---

## Leverage the GraphQL endpoint

```bash
@mcp.tool(title="Search Events", description="Search for events in EPR")
async def search_events(data: dict) -> str:
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
async def search_receivers(data: dict) -> str:
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
async def search_groups(data: dict) -> str:
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

---

## Add Danger

```bash
@mcp.tool(title="Create Event", description="Create a new event in EPR")
async def create_event(event_data: dict) -> str:
    """Create a new event in the EPR"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{epr_url}/api/v1/events", json=event_data)
        if response.status_code == 201:
            return "Event created successfully"
        else:
            return f"Failed to create event: {response.text}"

@mcp.tool(title="Create Event Receiver", description="Create a new event receiver in EPR")
async def create_receiver(receiver_data: dict) -> str:
    """Create a new event receiver in the EPR"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{epr_url}/api/v1/receivers", json=receiver_data)
        if response.status_code == 201:
            return "Event receiver created successfully"
        else:
            return f"Failed to create event receiver: {response.text}"

@mcp.tool(title="Create Event Receiver Group", description="Create a new event receiver group in EPR")
async def create_group(group_data: dict) -> str:
    """Create a new event receiver group in the EPR"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{epr_url}/api/v1/groups", json=group_data)
        if response.status_code == 201:
            return "Event receiver group created successfully"
        else:
            return f"Failed to create event receiver group: {response.text}"
```

---

## Re-Build the docker image

```bash
docker build -t epr-mcp-server:latest .
```

---

## Restart MCP Server

Restart your MCP server in MCP Inspector or VSCode to see results.

---

## Summary

Extending Your Server

- Add more tools for additional API endpoints.
- Implement authentication or custom error handling as needed.
- Use the `get_search_query` helper to build flexible search queries.

# SPDX-FileCopyrightText: © 2025 Brett Smith <xbcsmith@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import httpx2
from fastmcp import FastMCP

debug = bool(os.environ.get("EPR_DEBUG", False))
level = logging.DEBUG if debug else logging.INFO
log_format = "%(asctime)s %(name)s:[%(levelname)s] %(message)s"
# stdout carries the MCP protocol over stdio, so all logging goes to stderr.
logging.basicConfig(stream=sys.stderr, level=level, format=log_format)
logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration for the EPR MCP server."""

    url: str
    token: str
    debug: bool = False

    def as_dict(self) -> dict:
        """Return configuration as a dictionary."""
        return asdict(self)


@dataclass
class Model:
    """Base class for data objects."""

    def as_dict(self) -> dict:
        """Return object properties as a dictionary."""
        return asdict(self)

    def as_dict_query(self) -> dict:
        """Return non-None object properties as a dictionary."""
        return {k: v for k, v in self.as_dict().items() if v}


@dataclass
class GraphQLQuery(Model):
    """A GraphQL query with variables."""

    query: str
    variables: dict[str, Any] = field(default_factory=dict)


def get_operation(name: str, operation: str) -> str:
    """Look up the GraphQL type or operation name for an EPR resource.

    Args:
        name: The lookup table name (search, mutation, operation, create).
        operation: The key within that table.

    Returns:
        The corresponding GraphQL type or operation string.

    Examples:
        >>> get_operation("search", "events")
        'FindEventInput!'
    """
    operation_map = {
        "search": {
            "events": "FindEventInput!",
            "event_receivers": "FindEventReceiverInput!",
            "event_receiver_groups": "FindEventReceiverGroupInput!",
        },
        "mutation": {
            "create_event": "CreateEventInput!",
            "create_event_receiver": "CreateEventReceiverInput!",
            "create_event_receiver_group": "CreateEventReceiverGroupInput!",
        },
        "operation": {
            "events": "event",
            "event_receivers": "event_receiver",
            "event_receiver_groups": "event_receiver_group",
        },
        "create": {
            "create_event": "event",
            "create_event_receiver": "event_receiver",
            "create_event_receiver_group": "event_receiver_group",
        },
    }
    return operation_map[name][operation]


def get_search_query(operation: str, params: Optional[dict] = None, fields: Optional[list] = None) -> GraphQLQuery:
    """Build a GraphQL search query for an EPR resource.

    Args:
        operation: The EPR resource type (events, event_receivers, event_receiver_groups).
        params: Optional search criteria passed as GraphQL variables.
        fields: Fields to return; defaults to ["id"].

    Returns:
        A GraphQLQuery ready to POST to /api/v1/graphql/query.

    Examples:
        >>> q = get_search_query("events", {"name": "build"}, ["id", "name"])
    """
    variables = dict(obj=params)
    method = get_operation("search", operation)
    op = get_operation("operation", operation)
    _fields = ",".join(fields) if fields is not None else "id"
    query = f"query ($obj: {method}){{{operation}({op}: $obj) {{ {_fields} }}}}"
    return GraphQLQuery(query=query, variables=variables)


def get_mutation_query(operation: str, params: Optional[dict] = None) -> GraphQLQuery:
    """Build a GraphQL mutation query to create an EPR resource.

    Args:
        operation: The create operation (create_event, create_event_receiver,
            create_event_receiver_group).
        params: Optional fields for the new resource.

    Returns:
        A GraphQLQuery ready to POST to /api/v1/graphql/query.

    Examples:
        >>> q = get_mutation_query("create_event", {"name": "build"})
    """
    variables = dict(obj=params)
    method = get_operation("mutation", operation)
    op = get_operation("create", operation)
    query = f"mutation ($obj: {method}){{{operation}({op}: $obj)}}"
    return GraphQLQuery(query=query, variables=variables)


cfg = Config(
    url=os.environ.get("EPR_URL", "http://localhost:8042"),
    token=os.environ.get("EPR_TOKEN", ""),
    debug=debug,
)

mcp = FastMCP(name="epr-workshop-mcp")


@mcp.tool(title="Fetch Event", description="Fetch an event from EPR")
async def fetch_event(id: str) -> str:
    """Fetch an event from the EPR by its ID.

    Args:
        id: The event's ID.

    Returns:
        The event as JSON text.

    Examples:
        >>> # call_tool("fetch_event", {"id": "01JYRZ96R690ZTQ15Q53GEY6E6"})
    """
    async with httpx2.AsyncClient() as client:
        response = await client.get(f"{cfg.url}/api/v1/events/{id}")
        return response.text


@mcp.tool(title="Fetch Event Receiver", description="Fetch an event receiver from EPR")
async def fetch_receiver(id: str) -> str:
    """Fetch an event receiver from the EPR by its ID.

    Args:
        id: The event receiver's ID.

    Returns:
        The event receiver as JSON text.

    Examples:
        >>> # call_tool("fetch_receiver", {"id": "01JYRZ96R690ZTQ15Q53GEY6E6"})
    """
    async with httpx2.AsyncClient() as client:
        response = await client.get(f"{cfg.url}/api/v1/receivers/{id}")
        return response.text


@mcp.tool(title="Fetch Event Receiver Group", description="Fetch an event receiver group from EPR")
async def fetch_group(id: str) -> str:
    """Fetch an event receiver group from the EPR by its ID.

    Args:
        id: The event receiver group's ID.

    Returns:
        The event receiver group as JSON text.

    Examples:
        >>> # call_tool("fetch_group", {"id": "01JYRZ96R690ZTQ15Q53GEY6E6"})
    """
    async with httpx2.AsyncClient() as client:
        response = await client.get(f"{cfg.url}/api/v1/groups/{id}")
        return response.text


@mcp.tool(title="Search Events", description="Search for events in EPR")
async def search_events(data: dict) -> str:
    """Search for events in the EPR using GraphQL.

    Args:
        data: Search criteria (name, version, release, platform_id, package,
            description, success, event_receiver_id).

    Returns:
        Matching events as JSON text, or an error message.

    Examples:
        >>> # call_tool("search_events", {"data": {"name": "build"}})
    """
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
    async with httpx2.AsyncClient() as client:
        headers = {"Content-Type": "application/json"}
        response = await client.post(f"{cfg.url}/api/v1/graphql/query", json=query.as_dict_query(), headers=headers)
        if response.status_code == 200:
            return response.text
        return f"Failed to search events: {response.text}"


@mcp.tool(title="Search Event Receivers", description="Search for event receivers in EPR")
async def search_receivers(data: dict) -> str:
    """Search for event receivers in the EPR using GraphQL.

    Args:
        data: Search criteria (name, type, version, description).

    Returns:
        Matching event receivers as JSON text, or an error message.

    Examples:
        >>> # call_tool("search_receivers", {"data": {"name": "ci"}})
    """
    fields = ["id", "name", "type", "version", "description"]
    query = get_search_query(operation="event_receivers", params=data, fields=fields)
    async with httpx2.AsyncClient() as client:
        headers = {"Content-Type": "application/json"}
        response = await client.post(f"{cfg.url}/api/v1/graphql/query", json=query.as_dict_query(), headers=headers)
        if response.status_code == 200:
            return response.text
        return f"Failed to search event receivers: {response.text}"


@mcp.tool(title="Search Event Receiver Groups", description="Search for event receiver groups in EPR")
async def search_groups(data: dict) -> str:
    """Search for event receiver groups in the EPR using GraphQL.

    Args:
        data: Search criteria (name, type, version, description).

    Returns:
        Matching event receiver groups as JSON text, or an error message.

    Examples:
        >>> # call_tool("search_groups", {"data": {"name": "ci"}})
    """
    fields = ["id", "name", "type", "version", "description"]
    query = get_search_query(operation="event_receiver_groups", params=data, fields=fields)
    async with httpx2.AsyncClient() as client:
        headers = {"Content-Type": "application/json"}
        response = await client.post(f"{cfg.url}/api/v1/graphql/query", json=query.as_dict_query(), headers=headers)
        if response.status_code == 200:
            return response.text
        return f"Failed to search event receiver groups: {response.text}"


@mcp.tool(title="Create Event", description="Create a new event in EPR")
async def create_event(event_data: dict) -> str:
    """Create a new event in the EPR.

    Args:
        event_data: Fields for the new event.

    Returns:
        "Event created successfully" or an error message.

    Examples:
        >>> # call_tool("create_event", {"event_data": {...}})
    """
    async with httpx2.AsyncClient() as client:
        response = await client.post(f"{cfg.url}/api/v1/events", json=event_data)
        if response.status_code == 201:
            return "Event created successfully"
        return f"Failed to create event: {response.text}"


@mcp.tool(title="Create Event Receiver", description="Create a new event receiver in EPR")
async def create_receiver(receiver_data: dict) -> str:
    """Create a new event receiver in the EPR.

    Args:
        receiver_data: Fields for the new event receiver.

    Returns:
        "Event receiver created successfully" or an error message.

    Examples:
        >>> # call_tool("create_receiver", {"receiver_data": {...}})
    """
    async with httpx2.AsyncClient() as client:
        response = await client.post(f"{cfg.url}/api/v1/receivers", json=receiver_data)
        if response.status_code == 201:
            return "Event receiver created successfully"
        return f"Failed to create event receiver: {response.text}"


@mcp.tool(title="Create Event Receiver Group", description="Create a new event receiver group in EPR")
async def create_group(group_data: dict) -> str:
    """Create a new event receiver group in the EPR.

    Args:
        group_data: Fields for the new event receiver group.

    Returns:
        "Event receiver group created successfully" or an error message.

    Examples:
        >>> # call_tool("create_group", {"group_data": {...}})
    """
    async with httpx2.AsyncClient() as client:
        response = await client.post(f"{cfg.url}/api/v1/groups", json=group_data)
        if response.status_code == 201:
            return "Event receiver group created successfully"
        return f"Failed to create event receiver group: {response.text}"


if __name__ == "__main__":
    logger.info("MCP is running with the following configuration:")
    logger.info("URL: %s", cfg.url)
    logger.info("Token configured: %s", bool(cfg.token))
    mcp.run(show_banner=False)

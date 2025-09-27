# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: © 2025 Brett Smith <xbcsmith@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP


def debug_except_hook(type, value, tb):
    print(f"epr python hates {type.__name__}")
    print(str(type))
    import pdb
    import traceback

    traceback.print_exception(type, value, tb)
    pdb.post_mortem(tb)


debug = bool(os.environ.get("EPR_DEBUG", False))
level = logging.INFO
if debug:
    sys.excepthook = debug_except_hook
    level = logging.DEBUG
log_format = "%(asctime)s %(name)s:[%(levelname)s] %(message)s"
logging.basicConfig(stream=sys.stderr, level=level, format=log_format)
logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Data class for Config"""

    url: str
    token: str
    debug: bool = False

    def as_dict(self):
        """Get a dictionary containing object properties"""
        return asdict(self)


@dataclass
class Model:
    """Base class for data objects. Provides as_dict"""

    def as_dict(self):
        """Get a dictionary contain object properties"""
        return asdict(self)

    def as_dict_query(self):
        """Get a dictionary contain object properties"""
        return {k: v for k, v in self.as_dict().items() if v}


@dataclass
class GraphQLQuery(Model):
    query: str
    variables: Dict[str, Any] = field(default_factory=dict)


def get_operation(name: str, operation: str) -> str:
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
    """Convert a query dictionary to a GraphQL query string."""
    variables = dict(obj=params)
    method = get_operation("search", operation)
    op = get_operation("operation", operation)
    _fields = ",".join(fields) if fields is not None else "id"
    query = f"""query ($obj: {method}){{{operation}({op}: $obj) {{ {_fields} }}}}"""
    return GraphQLQuery(query=query, variables=variables)


def get_mutation_query(operation: str, params: Optional[dict] = None) -> GraphQLQuery:
    """Convert a mutation dictionary to a GraphQL mutation string."""
    variables = dict(obj=params)
    method = get_operation("mutation", operation)
    op = get_operation("create", operation)
    query = f"""mutation ($obj: {method}){{{operation}({op}: $obj)}}"""
    return GraphQLQuery(query=query, variables=variables)


cfg = Config(
    url=os.environ.get("EPR_URL", "http://localhost:8042"), token=os.environ.get("EPR_TOKEN", "changeme"), debug=debug
)


mcp = FastMCP("epr-workshop-mcp")


@mcp.tool(title="Fetch Event", description="Fetch an event from EPR")
async def fetch_event(epr_url: str, id: str) -> str:
    """Fetch an event from the EPR"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{epr_url}/api/v1/events/{id}")
        return response.text


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


"""Run the MCP"""
logger.info("MCP is running with the following configuration:")
logger.info(f"URL: {cfg.url}")
logger.info(f"Token: {cfg.token}")
mcp.run()

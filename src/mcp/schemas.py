# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: © 2025 Brett Smith <xbcsmith@gmail.com>
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator, ValidationError


class EventSearchInput(BaseModel):
    """Schema for event search input"""
    name: Optional[str] = Field(None, description="Name of the event")
    version: Optional[str] = Field(None, description="Version of the event")
    release: Optional[str] = Field(None, description="Release version")
    platform_id: Optional[str] = Field(None, description="Platform identifier")
    package: Optional[str] = Field(None, description="Package name")
    description: Optional[str] = Field(None, description="Event description")
    success: Optional[bool] = Field(None, description="Success status")
    event_receiver_id: Optional[str] = Field(None, description="Event receiver ID")


class EventReceiverSearchInput(BaseModel):
    """Schema for event receiver search input"""
    name: Optional[str] = Field(None, description="Name of the event receiver")
    type: Optional[str] = Field(None, description="Type of the event receiver")
    version: Optional[str] = Field(None, description="Version of the event receiver")
    description: Optional[str] = Field(None, description="Event receiver description")


class EventReceiverGroupSearchInput(BaseModel):
    """Schema for event receiver group search input"""
    name: Optional[str] = Field(None, description="Name of the event receiver group")
    type: Optional[str] = Field(None, description="Type of the event receiver group")
    version: Optional[str] = Field(None, description="Version of the event receiver group")
    description: Optional[str] = Field(None, description="Event receiver group description")


class SearchDataWrapper(BaseModel):
    """Wrapper for search data input"""
    data: Union[EventSearchInput, EventReceiverSearchInput, EventReceiverGroupSearchInput] = Field(
        ..., description="Search criteria data"
    )


class EventCreateInput(BaseModel):
    """Schema for event creation input"""
    name: str = Field(..., description="Name of the event", min_length=1)
    version: str = Field(..., description="Version of the event", min_length=1)
    release: str = Field(..., description="Release version", min_length=1)
    platform_id: str = Field(..., description="Platform identifier", min_length=1)
    package: str = Field(..., description="Package name", min_length=1)
    description: str = Field(..., description="Event description", min_length=1)
    event_receiver_id: str = Field(..., description="Event receiver ID", min_length=1)
    success: bool = Field(..., description="Success status")
    payload: Dict[str, Any] = Field(..., description="Event payload data")

    @validator('payload')
    def validate_payload(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Payload must be a dictionary')
        return v


class EventReceiverCreateInput(BaseModel):
    """Schema for event receiver creation input"""
    name: str = Field(..., description="Name of the event receiver", min_length=1)
    type: str = Field(..., description="Type of the event receiver", min_length=1)
    version: str = Field(..., description="Version of the event receiver", min_length=1)
    description: str = Field(..., description="Event receiver description", min_length=1)


class EventReceiverGroupCreateInput(BaseModel):
    """Schema for event receiver group creation input"""
    name: str = Field(..., description="Name of the event receiver group", min_length=1)
    type: str = Field(..., description="Type of the event receiver group", min_length=1)
    version: str = Field(..., description="Version of the event receiver group", min_length=1)
    description: str = Field(..., description="Event receiver group description", min_length=1)
    event_receiver_ids: List[str] = Field(..., description="List of event receiver IDs")

    @validator('event_receiver_ids')
    def validate_event_receiver_ids(cls, v):
        if not v:  # Check if list is empty
            raise ValueError('Event receiver IDs list cannot be empty')
        if not all(isinstance(id_str, str) and len(id_str.strip()) > 0 for id_str in v):
            raise ValueError('All event receiver IDs must be non-empty strings')
        return v


class EventCreateDataWrapper(BaseModel):
    """Wrapper for event creation data input"""
    data: EventCreateInput = Field(..., description="Event creation data")


class EventReceiverCreateDataWrapper(BaseModel):
    """Wrapper for event receiver creation data input"""
    data: EventReceiverCreateInput = Field(..., description="Event receiver creation data")


class EventReceiverGroupCreateDataWrapper(BaseModel):
    """Wrapper for event receiver group creation data input"""
    data: EventReceiverGroupCreateInput = Field(..., description="Event receiver group creation data")


class FetchInput(BaseModel):
    """Schema for fetch operations input"""
    id: str = Field(..., description="Resource ID to fetch", min_length=1)

    @validator('id')
    def validate_id(cls, v):
        if not v or not v.strip():
            raise ValueError('ID cannot be empty')
        return v.strip()


# Schema mapping for different operations
SCHEMA_MAP = {
    # Search operations
    "search_events": SearchDataWrapper,
    "search_receivers": SearchDataWrapper,
    "search_groups": SearchDataWrapper,
    
    # Create operations
    "create_event": EventCreateDataWrapper,
    "create_receiver": EventReceiverCreateDataWrapper,
    "create_group": EventReceiverGroupCreateDataWrapper,
    
    # Fetch operations
    "fetch_event": FetchInput,
    "fetch_receiver": FetchInput,
    "fetch_group": FetchInput,
}


def validate_input(operation: str, input_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate input data for a given operation.
    
    Args:
        operation: The operation name (e.g., 'search_events', 'create_event')
        input_data: The input data to validate
        
    Returns:
        Validated data as a dictionary
        
    Raises:
        ValueError: If the operation is not supported or validation fails
        ValidationError: If the input data doesn't match the schema
    """
    if operation not in SCHEMA_MAP:
        raise ValueError(f"Unsupported operation: {operation}")
    
    schema_class = SCHEMA_MAP[operation]
    
    # For fetch operations, the input is just an ID string
    if operation.startswith("fetch_"):
        validated = schema_class(id=input_data)
        return {"id": validated.id}
    
    # For other operations, validate the full structure
    if not isinstance(input_data, dict):
        raise ValueError(f"Input data for {operation} must be a dictionary")
    validated = schema_class(**input_data)
    return validated.dict()


def get_validation_schema(operation: str) -> BaseModel:
    """
    Get the validation schema class for a given operation.
    
    Args:
        operation: The operation name
        
    Returns:
        The Pydantic model class for validation
        
    Raises:
        ValueError: If the operation is not supported
    """
    if operation not in SCHEMA_MAP:
        raise ValueError(f"Unsupported operation: {operation}")
    
    return SCHEMA_MAP[operation]
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: © 2025 Brett Smith <xbcsmith@gmail.com>
# SPDX-License-Identifier: Apache-2.0

"""
Example usage of the EPR MCP Server schema validation system
"""

from pydantic import ValidationError
from schemas import validate_input, get_validation_schema


def example_search_events():
    """Example of searching events with validation"""
    print("=== Search Events Example ===")
    
    # Valid search input
    search_data = {
        "data": {
            "name": "foo",
            "version": "1.0.0"
        }
    }
    
    try:
        validated = validate_input("search_events", search_data)
        print("✓ Search validation passed")
        print(f"  Query parameters: {validated['data']}")
        
        # This is how you would use it in the MCP tool
        # query = get_search_query(operation="events", data=validated, fields=fields)
        
    except (ValidationError, ValueError) as e:
        print(f"✗ Search validation failed: {e}")


def example_create_event():
    """Example of creating an event with validation"""
    print("\n=== Create Event Example ===")
    
    # Valid create input
    create_data = {
        "data": {
            "name": "my-test-event",
            "version": "2.1.0",
            "release": "2025.01.005",
            "platform_id": "x64-linux-oci-3",
            "package": "my-package",
            "description": "Test event for demonstration",
            "event_receiver_id": "01K6RJPGX3JXMM8XJHYKQBGRXT",
            "success": True,
            "payload": {
                "build_id": "build-12345",
                "commit_sha": "abc123def456",
                "branch": "main",
                "duration_seconds": 120
            }
        }
    }
    
    try:
        validated = validate_input("create_event", create_data)
        print("✓ Create validation passed")
        print(f"  Event name: {validated['data']['name']}")
        print(f"  Payload keys: {list(validated['data']['payload'].keys())}")
        
        # This is how you would use it in the MCP tool
        # params = validated['data']
        # response = await client.post(f"{cfg.url}/api/v1/events", json=params)
        
    except (ValidationError, ValueError) as e:
        print(f"✗ Create validation failed: {e}")


def example_fetch_event():
    """Example of fetching an event with validation"""
    print("\n=== Fetch Event Example ===")
    
    # Valid fetch input (just an ID string)
    event_id = "01K6RJPGZSMHDMKH8VDB3PSBF2"
    
    try:
        validated = validate_input("fetch_event", event_id)
        print("✓ Fetch validation passed")
        print(f"  Event ID: {validated['id']}")
        
        # This is how you would use it in the MCP tool
        # response = await client.get(f"{cfg.url}/api/v1/events/{validated['id']}")
        
    except (ValidationError, ValueError) as e:
        print(f"✗ Fetch validation failed: {e}")


def example_create_receiver_group():
    """Example of creating an event receiver group with validation"""
    print("\n=== Create Event Receiver Group Example ===")
    
    # Valid group create input
    group_data = {
        "data": {
            "name": "ci-cd-pipeline-group",
            "type": "pipeline-processing",
            "version": "1.2.0",
            "description": "Group for handling CI/CD pipeline events",
            "event_receiver_ids": [
                "01K6RJPGX3JXMM8XJHYKQBGRXT",
                "01K6RJPGXF7EGDMSQ5X5CEFVTF",
                "01K6RJPGXP9BD165015CA74P5G"
            ]
        }
    }
    
    try:
        validated = validate_input("create_group", group_data)
        print("✓ Group creation validation passed")
        print(f"  Group name: {validated['data']['name']}")
        print(f"  Receiver count: {len(validated['data']['event_receiver_ids'])}")
        
        # This is how you would use it in the MCP tool
        # params = validated['data']
        # response = await client.post(f"{cfg.url}/api/v1/groups", json=params)
        
    except (ValidationError, ValueError) as e:
        print(f"✗ Group creation validation failed: {e}")


def example_error_handling():
    """Example of how validation errors are handled"""
    print("\n=== Error Handling Examples ===")
    
    # Missing required field
    print("\n1. Missing required field:")
    invalid_event = {
        "data": {
            "name": "incomplete-event",
            "version": "1.0.0"
            # Missing: release, platform_id, package, description, event_receiver_id, success, payload
        }
    }
    
    try:
        validate_input("create_event", invalid_event)
        print("✗ Should have failed!")
    except (ValidationError, ValueError) as e:
        print(f"✓ Correctly caught missing fields: {e}")
    
    # Empty string for required field
    print("\n2. Empty ID string:")
    try:
        validate_input("fetch_event", "")
        print("✗ Should have failed!")
    except (ValidationError, ValueError) as e:
        print(f"✓ Correctly caught empty ID: {e}")
    
    # Empty list for required list field
    print("\n3. Empty receiver IDs list:")
    invalid_group = {
        "data": {
            "name": "empty-group",
            "type": "test",
            "version": "1.0.0",
            "description": "Test group",
            "event_receiver_ids": []  # Empty list not allowed
        }
    }
    
    try:
        validate_input("create_group", invalid_group)
        print("✗ Should have failed!")
    except (ValidationError, ValueError) as e:
        print(f"✓ Correctly caught empty list: {e}")


def show_schema_info():
    """Display information about available schemas"""
    print("\n=== Available Schema Operations ===")
    
    from schemas import SCHEMA_MAP
    
    for operation, schema_class in SCHEMA_MAP.items():
        print(f"  {operation}: {schema_class.__name__}")
        
        # Get schema info
        try:
            schema = get_validation_schema(operation)
            print(f"    → {schema.__doc__ or 'Validation schema'}")
        except ValueError as e:
            print(f"    → Error: {e}")


if __name__ == "__main__":
    print("EPR MCP Server Schema Validation Examples")
    print("=" * 50)
    
    example_search_events()
    example_create_event()
    example_fetch_event()
    example_create_receiver_group()
    example_error_handling()
    show_schema_info()
    
    print("\n" + "=" * 50)
    print("Schema validation examples completed!")
    print("See SCHEMA_VALIDATION.md for detailed documentation.")
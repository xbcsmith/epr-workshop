# MCP Server Input Validation

In this section, we'll enhance our EPR MCP Server by adding robust input
validation using Pydantic schemas. This will improve error handling, data
integrity, and security.

## Learning Objectives

By the end of this section, you will:

- Understand the importance of input validation in MCP servers
- Create Pydantic schemas for validating tool inputs
- Implement validation in MCP tool handlers
- Handle validation errors gracefully
- Test your validation implementation

---

## Why Input Validation Matters

Without proper input validation, MCP tools can:

- Crash with unclear error messages
- Process malformed data leading to unexpected behavior
- Be vulnerable to injection attacks
- Provide poor user experience with cryptic errors

Input validation helps ensure:

- **Data Integrity**: Only valid data reaches your business logic
- **Security**: Prevents malicious or malformed inputs
- **User Experience**: Clear, helpful error messages
- **Documentation**: Schemas serve as living documentation

---

## Install Pydantic

First, let's add Pydantic as a dependency to our project.

Update the `pyproject.toml` file:

```bash
cd /home/bsmith/go/src/github.com/xbcsmith/epr-workshop/11-epr-mcp-server/src
```

Add Pydantic to your dependencies in `pyproject.toml`:

```toml
[project]
dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.25.0",
    "pydantic>=2.0.0"
]
```

Install the new dependency:

```bash
pip install pydantic>=2.0.0
```

---

## Create Validation Schemas

Create a new file `schemas.py` to define our validation schemas:

```python
# schemas.py
from typing import Optional, Dict, List, Union, Any
from pydantic import BaseModel, Field, validator


class EventSearchInput(BaseModel):
    """Schema for searching events"""
    name: Optional[str] = Field(None, description="Event name to search for")
    version: Optional[str] = Field(None, description="Event version to search for")
    release: Optional[str] = Field(None, description="Release to search for")
    platform_id: Optional[str] = Field(None, description="Platform ID to search for")
    package: Optional[str] = Field(None, description="Package to search for")
    description: Optional[str] = Field(None, description="Description to search for")
    success: Optional[bool] = Field(None, description="Success status to search for")
    event_receiver_id: Optional[str] = Field(None, description="Event receiver ID to search for")


class EventReceiverSearchInput(BaseModel):
    """Schema for searching event receivers"""
    name: Optional[str] = Field(None, description="Receiver name to search for")
    type: Optional[str] = Field(None, description="Receiver type to search for")
    version: Optional[str] = Field(None, description="Receiver version to search for")
    description: Optional[str] = Field(None, description="Description to search for")


class EventReceiverGroupSearchInput(BaseModel):
    """Schema for searching event receiver groups"""
    name: Optional[str] = Field(None, description="Group name to search for")
    type: Optional[str] = Field(None, description="Group type to search for")
    version: Optional[str] = Field(None, description="Group version to search for")
    description: Optional[str] = Field(None, description="Description to search for")


class EventCreateInput(BaseModel):
    """Schema for creating events - all fields required"""
    name: str = Field(..., min_length=1, description="Event name (required)")
    version: str = Field(..., min_length=1, description="Event version (required)")
    release: str = Field(..., min_length=1, description="Release (required)")
    platform_id: str = Field(..., min_length=1, description="Platform ID (required)")
    package: str = Field(..., min_length=1, description="Package (required)")
    description: str = Field(..., min_length=1, description="Description (required)")
    event_receiver_id: str = Field(..., min_length=1, description="Event receiver ID (required)")
    success: bool = Field(..., description="Success status (required)")
    payload: Dict[str, Any] = Field(..., description="Event payload (required)")


class EventReceiverCreateInput(BaseModel):
    """Schema for creating event receivers - all fields required"""
    name: str = Field(..., min_length=1, description="Receiver name (required)")
    type: str = Field(..., min_length=1, description="Receiver type (required)")
    version: str = Field(..., min_length=1, description="Receiver version (required)")
    description: str = Field(..., min_length=1, description="Description (required)")


class EventReceiverGroupCreateInput(BaseModel):
    """Schema for creating event receiver groups - all fields required"""
    name: str = Field(..., min_length=1, description="Group name (required)")
    type: str = Field(..., min_length=1, description="Group type (required)")
    version: str = Field(..., min_length=1, description="Group version (required)")
    description: str = Field(..., min_length=1, description="Description (required)")
    event_receiver_ids: List[str] = Field(..., min_items=1, description="List of event receiver IDs (required)")

    @validator('event_receiver_ids')
    def validate_event_receiver_ids(cls, v):
        if not all(isinstance(item, str) and len(item.strip()) > 0 for item in v):
            raise ValueError('All event receiver IDs must be non-empty strings')
        return v


class FetchInput(BaseModel):
    """Schema for fetch operations"""
    id: str = Field(..., min_length=1, description="ID to fetch (required)")

    @validator('id')
    def validate_id(cls, v):
        return v.strip()


# Wrapper classes for data structures
class SearchDataWrapper(BaseModel):
    """Wrapper for search operations with data field"""
    data: Union[EventSearchInput, EventReceiverSearchInput, EventReceiverGroupSearchInput]


class CreateDataWrapper(BaseModel):
    """Wrapper for create operations with data field"""
    data: Union[EventCreateInput, EventReceiverCreateInput, EventReceiverGroupCreateInput]


# Schema mapping for different operations
SCHEMA_MAP = {
    "search_events": SearchDataWrapper,
    "search_receivers": SearchDataWrapper,
    "search_groups": SearchDataWrapper,
    "create_event": CreateDataWrapper,
    "create_receiver": CreateDataWrapper,
    "create_group": CreateDataWrapper,
    "fetch_event": FetchInput,
    "fetch_receiver": FetchInput,
    "fetch_group": FetchInput,
}


def validate_input(operation: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate input data for a given operation

    Args:
        operation: The operation name (e.g., 'search_events', 'create_event')
        input_data: The input data to validate

    Returns:
        Validated data as a dictionary

    Raises:
        ValueError: If operation is not supported
        ValidationError: If input data is invalid
    """
    if operation not in SCHEMA_MAP:
        raise ValueError(f"Unsupported operation: {operation}")

    schema_class = SCHEMA_MAP[operation]
    validated = schema_class(**input_data)
    return validated.dict()
```

---

## Update MCP Tools with Validation

Now let's update our `main.py` file to use the validation schemas:

```python
# main.py - Add imports at the top
from schemas import validate_input
from pydantic import ValidationError

# Update each tool to include validation
@mcp.tool(title="Search Events", description="Search for events in EPR")
async def search_events(data: dict) -> str:
    """Search for events with optional filters"""
    try:
        # Validate input data
        validated_data = validate_input("search_events", data)
        search_params = validated_data.get("data", {})
    except (ValidationError, ValueError) as e:
        return f"Error - Validation error: {str(e)}"

    try:
        response = await client.post(
            f"{EPR_BASE_URL}/events/search",
            json=search_params,
            timeout=30.0
        )
        response.raise_for_status()
        return f"Success - Events found:\n{format_json_response(response.json())}"
    except Exception as e:
        return f"Error - Error searching events: {str(e)}"


@mcp.tool(title="Create Event", description="Create a new event in EPR")
async def create_event(data: dict) -> str:
    """Create a new event"""
    try:
        # Validate input data
        validated_data = validate_input("create_event", data)
        event_data = validated_data.get("data", {})
    except (ValidationError, ValueError) as e:
        return f"Error - Validation error: {str(e)}"

    try:
        response = await client.post(
            f"{EPR_BASE_URL}/events",
            json=event_data,
            timeout=30.0
        )
        response.raise_for_status()
        return f"Success - Event created:\n{format_json_response(response.json())}"
    except Exception as e:
        return f"Error - Error creating event: {str(e)}"


@mcp.tool(title="Fetch Event", description="Fetch an event by ID")
async def fetch_event(id: str) -> str:
    """Fetch a specific event by ID"""
    try:
        # Validate input data
        validated_data = validate_input("fetch_event", {"id": id})
        event_id = validated_data["id"]
    except (ValidationError, ValueError) as e:
        return f"Error - Validation error: {str(e)}"

    try:
        response = await client.get(
            f"{EPR_BASE_URL}/events/{event_id}",
            timeout=30.0
        )
        response.raise_for_status()
        return f"Success - Event details:\n{format_json_response(response.json())}"
    except Exception as e:
        return f"Error - Error fetching event: {str(e)}"
```

---

## Apply Validation to All Tools

Update all remaining tools following the same pattern:

- `search_receivers` → use `"search_receivers"` operation
- `search_groups` → use `"search_groups"` operation
- `create_receiver` → use `"create_receiver"` operation
- `create_group` → use `"create_group"` operation
- `fetch_receiver` → use `"fetch_receiver"` operation
- `fetch_group` → use `"fetch_group"` operation

---

## Test Your Validation

Create a test file `test_schemas.py` to verify your validation works:

```python
# test_schemas.py
from schemas import validate_input
from pydantic import ValidationError

def test_valid_search():
    """Test valid search input"""
    try:
        result = validate_input("search_events", {
            "data": {
                "name": "foo",
                "version": "1.0.0"
            }
        })
        print("Success - Valid search input passed")
        return True
    except Exception as e:
        print(f"Error - Valid search failed: {e}")
        return False

def test_invalid_create():
    """Test invalid create input (missing required fields)"""
    try:
        validate_input("create_event", {
            "data": {
                "name": "test"
                # Missing required fields
            }
        })
        print("Error - Invalid create should have failed")
        return False
    except ValidationError:
        print("Success - Invalid create correctly rejected")
        return True
    except Exception as e:
        print(f"Error - Unexpected error: {e}")
        return False

def test_empty_string_validation():
    """Test empty string validation"""
    try:
        validate_input("fetch_event", {"id": ""})
        print("Error - Empty ID should have failed")
        return False
    except ValidationError:
        print("Success - Empty ID correctly rejected")
        return True
    except Exception as e:
        print(f"Error - Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Running validation tests...")
    tests = [test_valid_search, test_invalid_create, test_empty_string_validation]
    passed = sum(test() for test in tests)
    print(f"\n{passed}/{len(tests)} tests passed")
```

Run the tests:

```bash
python test_schemas.py
```

---

## Test with the MCP Server

Now let's test our enhanced MCP server with validation:

1. **Start the server**:

```bash
python main.py
```

2. **Test valid input** (should work):

```json
{
  "data": {
    "name": "foo",
    "version": "1.0.0"
  }
}
```

3. **Test invalid input** (should show validation error):

```json
{
  "data": {
    "name": "",
    "version": "1.0.0"
  }
}
```

---

## Understanding Validation Errors

When validation fails, you'll see clear error messages like:

```
Error - Validation error: 1 validation error for CreateDataWrapper
data -> name
  ensure this value has at least 1 characters (type=value_error.any_str.min_length; limit_value=1)
```

This tells you:

- Which field failed validation (`name`)
- What the problem is (minimum length requirement)
- What the limit is (at least 1 character)

---

## Re-Build the docker image

```bash
docker build -t epr-mcp-server:latest .
```

---

## Restart MCP Server

Restart your MCP server in MCP Inspector or VSCode to see results.

---

## Key Validation Rules

### Search Operations

- All fields are optional
- Used for filtering results
- Empty strings are allowed (means "don't filter by this field")

### Create Operations

- All fields are required (`...` in Field definition)
- Strings must have minimum length of 1 (`min_length=1`)
- Lists must have at least 1 item (`min_items=1`)
- Payload must be a valid dictionary

### Fetch Operations

- ID is required and must be non-empty
- Automatically trims whitespace

## Benefits You've Added

**Better Error Messages**: Users get clear feedback on what's wrong **Data
Safety**: Invalid data never reaches your business logic  
**Security**: Prevents injection attacks and malformed data **Documentation**:
Schemas document expected input formats **Type Safety**: Ensures correct data
types throughout your application

---

## Troubleshooting

**Common Issues:**

1. **ValidationError on valid data**: Check that your input matches the expected
   schema structure
2. **Missing data field**: Remember that search and create operations expect
   data to be wrapped in a `data` field
3. **Pydantic import errors**: Ensure you have Pydantic 2.0+ installed

**Debug Tips:**

- Print the validated data to see what's being processed
- Use the test file to verify your schemas work correctly
- Check the schema definitions match your expected input format

## Summary

You've successfully added robust input validation to your EPR MCP Server using
Pydantic schemas. This enhancement improves the reliability, security, and user
experience of your MCP tools while providing clear documentation of expected
input formats.

---

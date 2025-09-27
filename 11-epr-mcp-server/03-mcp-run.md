# Running EPR MCP Server

## Overview

In this section wee will hook up a live LLM to our MCP server. Several AI assistants and tools support MCP, including: VSCode, Claude Desktop, MCP Inspector.

### Connecting VSCode

## VSCode Config

In settings `settings.json` add the following configuration to enable MCP discovery and set up the MCP servers:


```json
    "chat.mcp.discovery.enabled": true,
```

And the `.github/mcp.json` file in the `.vscode` directory should look like this:

```json
{
    "inputs": [
        {
            "type": "promptString",
            "id": "epr_token",
            "description": "EPR API Token",
            "password": true
        },
        {
            "type": "promptString",
            "id": "epr_url",
            "description": "EPR URL",
            "default": "http://localhost:8042",
            "password": false
        }
    ],
    "servers": {
        "epr-mcp-server": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "-e",
                "EPR_URL",
                "-e",
                "EPR_TOKEN",
                "epr-mcp-server:latest",
            ],
            "env": {
                "EPR_URL": "${input:epr_url}",
                "EPR_TOKEN": "${input:epr_token}"
            }
        }
    }
}
```

Adding the MCP servers directly to the `settings.json` file looks like this:

```json
    "chat.mcp.discovery.enabled": true,
    "mcp": {
        "inputs": [
            {
                "type": "promptString",
                "id": "epr_token",
                "description": "EPR API Token",
                "password": true
            },
            {
                "type": "promptString",
                "id": "epr_url",
                "description": "EPR URL",
                "default": "http://localhost:8042",
                "password": false
            }
        ],
        "servers": {
        "epr-mcp-server": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "-e",
                "EPR_URL",
                "-e",
                "EPR_TOKEN",
                "epr-mcp-server:latest",
            ],
            "env": {
                "EPR_URL": "${input:epr_url}",
                "EPR_TOKEN": "${input:epr_token}"
            }
        }
        }
    },
```

### Connecting with Claude desktop

Anthropic’s Claude Desktop application has built-in support for local MCP servers. To integrate:

```bash
mcp install ./main.py
```

This registers your server with Claude. In Claude’s interface, you should see your “To-Do API MCP Server” available. Now when you have a conversation with Claude, you can:

Ask: “List my to-do tasks” - Claude will use the todo://list resource
Request: “Add a to-do item to buy milk” - Claude will use the add_task tool

Claude will handle running the MCP server and routing requests when the AI decides to use it.
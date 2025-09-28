# Running EPR MCP Server

## Overview

In this section we will cover connecting the EPR MCP server to AI assistants and
development tools that support Model Context Protocol integration. The setup
enables natural language interaction with EPR systems through tools like VSCode,
Claude Desktop, and MCP Inspector.

---

## Connecting VSCode

The section provides two configuration approaches for integrating the EPR MCP
server with VSCode's chat functionality. The first approach uses a separate
.vscode/mcp.json configuration file that defines input prompts for EPR URL and
API token, along with server configuration that runs the MCP server via Docker.
The second approach embeds the same configuration directly in VSCode's
settings.json file. Both configurations use Docker to run the MCP server with
environment variables for EPR_URL and EPR_TOKEN, enabling secure credential
management through VSCode's input system. The setup includes password masking
for the API token and a default localhost URL for development environments.

---

### VSCode Config

In settings `settings.json` add the following configuration to enable MCP
discovery and set up the MCP servers:

```json
    "chat.mcp.discovery.enabled": true,
```

And the `.github/mcp.json` file in the `.vscode` directory should look like
this:

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
        "epr-mcp-server:latest"
      ],
      "env": {
        "EPR_URL": "${input:epr_url}",
        "EPR_TOKEN": "${input:epr_token}"
      }
    }
  }
}
```

---

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

---

## Connecting with Claude desktop

This section covers Claude Desktop's built-in MCP support, showing a command to
register the server (mcp install ./main.py). Once registered, users can interact
with EPR through natural language queries in Claude's interface, such as
requesting to list events or create new receivers.

Anthropic’s Claude Desktop application has built-in support for local MCP
servers. To integrate:

```bash
mcp install ./main.py
```

This registers your server with Claude. In Claude’s interface, you should see
your “EPR MCP Server” available. Now when you have a conversation with Claude,
you can:

Ask: list tools

Claude will handle running the MCP server and routing requests when the AI
decides to use it.

---

## Summary

The configuration enables seamless integration between AI assistants and the EPR
system, allowing users to query events, manage receivers, and perform other EPR
operations through conversational interfaces rather than direct API calls or CLI
commands. The Docker-based deployment ensures consistent execution across
different development environments.

---

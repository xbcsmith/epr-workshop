# Running EPR MCP Server

## Overview

In this section we will cover connecting the EPR MCP server to AI assistants and
development tools that support Model Context Protocol integration. The setup
enables natural language interaction with EPR systems through tools like VS
Code, Claude Desktop, and Zed.

---

## Running locally with uv

The simplest way to test your server is to run it directly on your machine. No
Docker required.

```bash
uv run python main.py
```

The server starts and waits for MCP protocol messages on stdin. Press Ctrl-C to
stop it.

---

## Connecting VS Code

The section provides two configuration approaches for integrating the EPR MCP
server with VS Code's chat functionality. The first approach uses a separate
`.vscode/mcp.json` configuration file that defines input prompts for EPR URL and
API token, along with server configuration that runs the MCP server via Docker.
The second approach embeds the same configuration directly in VS Code's
`settings.json` file. Both configurations use Docker to run the MCP server with
environment variables for `EPR_URL` and `EPR_TOKEN`, enabling secure credential
management through VS Code's input system. The setup includes password masking
for the API token and a default localhost URL for development environments.

---

### VS Code Config

In `settings.json` add the following configuration to enable MCP discovery and
set up the MCP servers:

```json
"chat.mcp.discovery.enabled": true,
```

And the `.vscode/mcp.json` file should look like this:

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
      "default": "http://host.docker.internal:8042",
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
            "default": "http://host.docker.internal:8042",
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
                "--network=host",
                "-e",
                "HOST",
                "-e",
                "EPR_URL",
                "-e",
                "EPR_TOKEN",
                "epr-mcp-server:latest"
            ],
            "env": {
                "EPR_URL": "http://host.docker.internal:8042",
                "EPR_TOKEN": "${input:epr_token}",
                "HOST": "0.0.0.0"
            },
            "type": "stdio"
        }
    }
}
```

---

## Connecting with Claude Desktop

Edit Claude Desktop's configuration file directly.

On macOS the file is at:
`~/Library/Application Support/Claude/claude_desktop_config.json`

Add the server entry:

```json
{
  "mcpServers": {
    "epr-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network=host",
        "-e",
        "EPR_URL",
        "-e",
        "EPR_TOKEN",
        "epr-mcp-server:latest"
      ],
      "env": {
        "EPR_URL": "http://localhost:8042"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

Alternatively, for a local (non-Docker) server:

```json
{
  "mcpServers": {
    "epr-mcp-server": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/work", "python", "main.py"],
      "env": {
        "EPR_URL": "http://localhost:8042"
      }
    }
  }
}
```

---

## Connecting with Zed

Add the server to your Zed `settings.json` under `context_servers` using the
same `command` and `args` pattern as the VS Code config.

---

## Summary

The Docker-based deployment ensures consistent execution. For local development,
`uv run python main.py` also works.

---

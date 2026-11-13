# 11 EPR MCP Server

This module teaches you how to build an MCP server in Python that connects an AI
assistant to an Event Provenance Registry (EPR). It uses FastMCP 4 and httpx2.

## Modules

| File                | Topic                                    |
| ------------------- | ---------------------------------------- |
| 00_intro.md         | What MCP servers are and why they matter |
| 01_mcp_server.md    | Build a basic server with one tool       |
| 02_mcp_inspector.md | Test tools with the MCP Inspector        |
| 03_mcp_run.md       | Connect the server to VS Code and Claude |
| 04_mcp_extended.md  | Add all nine EPR tools                   |
| 05_mcp_misc.md      | uv tips and alternative run commands     |

## Source

The finished server is at `src/mcp/main.py`. It uses FastMCP 4 and httpx2.

## Prerequisites

- Python 3.12 or later
- uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Node.js (for MCP Inspector: `npx @modelcontextprotocol/inspector`)
- Docker (optional, for the containerised demo path)
- A running EPR instance (`EPR_URL` environment variable)

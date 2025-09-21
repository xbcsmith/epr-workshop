# Testing EPR MCP Server



## Connect the MCP server to an LLM client

Now let’s hook up a live LLM to our MCP server. Several AI assistants and tools support MCP, including:

### Connecting with Claude desktop

Anthropic’s Claude Desktop application has built-in support for local MCP servers. To integrate:

```bash
mcp install ./todo_mcp_server.py
```

This registers your server with Claude. In Claude’s interface, you should see your “To-Do API MCP Server” available. Now when you have a conversation with Claude, you can:

Ask: “List my to-do tasks” - Claude will use the todo://list resource
Request: “Add a to-do item to buy milk” - Claude will use the add_task tool

Claude will handle running the MCP server and routing requests when the AI decides to use it.

### Connecting VSCode


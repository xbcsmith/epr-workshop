# EPR MCP Miscellaneous

## Miscellaneous Commands and Info

Random info that could be helpful

## Alternative UV

UV - An extremely fast Python package and project manager, written in Rust.

[Docs](https://docs.astral.sh/uv)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
export UV_INDEX_URL=$PIP_INDEX_URL
```

```bash
cd src/
uv venv
source .venv/bin/activate
uv add "mcp[cli]" mcp httpx
```

## Altenative Run Commands

To run the MCP server, use the following command:

```bash 
docker run -i --rm --network=host -e EPR_URL -e EPR_TOKEN epr-mcp-server:latest
```

```bash
mcp dev main.py
```

```bash
uv run --with mcp --with mcp[cli] --with pydantic --with httpx mcp run main.py
```
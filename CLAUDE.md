# CLAUDE.md — Project Context for Claude/Copilot

## Project Overview

MCP Manager is a Python MCP server that helps discover, evaluate, and manage MCP servers. It searches the official MCP Registry, evaluates trust via GitHub, and filters out servers that duplicate functionality already built into pi/Craft Agents.

## Quick Commands

```bash
# Install
uv sync
uv pip install -e .

# Run
python -m mcp_manager.server

# Test tools
python -c "
import asyncio
from mcp_manager.server import server
async def main():
    tools = await server.list_tools()
    print(f'{len(tools)} tools registered')
    for t in sorted(tools, key=lambda x: x.name):
        print(f'  - {t.name}')
asyncio.run(main())
"
```

## Project Structure

```
mcp-manager/
├── pyproject.toml
├── README.md
├── ARCHITECTURE.md
├── AGENTS.md
├── CLAUDE.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── SKILL.md
├── src/mcp_manager/
│   ├── server.py              ← Main server (10 tools)
│   ├── data/
│   │   └── capabilities.json  ← pi built-in capability map
│   └── utils/
│       ├── config.py          ← .mcp.json read/write
│       ├── github.py          ← GitHub API + trust score
│       ├── registry.py        ← MCP Registry API client
│       └── capabilities.py    ← Redundancy + value scoring
└── .gitignore
```

## Key Design Decisions

1. **FastMCP over raw SDK** — cleaner decorator-based API for tool registration
2. **Sync utilities** — httpx HTTP calls are synchronous (simpler, no asyncio overhead for I/O-bound tasks)
3. **Static JSON for capabilities** — easy to edit without touching Python code
4. **Composite score** — balances trust (40%), non-redundancy (30%), and value (30%)
5. **Default dry-run** — config generation never writes without explicit opt-in

## Dependencies

- `mcp[cli]>=1.27.0` — FastMCP server framework
- `httpx>=0.28.1` — HTTP client

## Environment Variables

- `GITHUB_TOKEN` — optional, for 5,000 req/h GitHub API (default: 60 req/h)
- `MCP_CONFIG_PATH` — optional, override `.mcp.json` location

## Current Tools (10)

1. list_local_servers
2. search_registry
3. get_server_details
4. assess_trustworthiness
5. search_with_trust
6. search_useful_mcp
7. generate_mcp_config
8. compare_alternatives
9. audit_workspace_mcp
10. registry_health

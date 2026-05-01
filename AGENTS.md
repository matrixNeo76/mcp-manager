# AGENTS.md — Instructions for AI Agents

This file provides context and instructions for any AI agent (Claude, Copilot, Cursor, etc.) working on this repository.

## Project Identity

- **Name**: MCP Manager (`mcp-manager`)
- **Purpose**: MCP server for discovering, evaluating, and managing other MCP servers
- **Repository**: `matrixNeo76/mcp-manager`
- **Language**: Python 3.12+
- **Framework**: FastMCP (via `mcp[cli]`)
- **Package Manager**: `uv`

## Key Files

| File | Purpose |
|------|---------|
| `src/mcp_manager/server.py` | Main FastMCP server — all 10 tools registered here |
| `src/mcp_manager/utils/config.py` | Reads/writes `.mcp.json` |
| `src/mcp_manager/utils/github.py` | GitHub API client + trust score computation |
| `src/mcp_manager/utils/registry.py` | MCP Registry API client |
| `src/mcp_manager/utils/capabilities.py` | Redundancy + value scoring engine |
| `src/mcp_manager/data/capabilities.json` | Static map of pi built-in capabilities |
| `SKILL.md` | Usage documentation for the MCP server |

## Architecture Rules

1. **All tools are async functions** decorated with `@server.tool()`
2. **Utilities are pure sync functions** in `utils/` — no async needed for HTTP calls
3. **Capabilities data is static JSON** — edit `data/capabilities.json` to add new categories
4. **Trust score** uses formula: 70% stars + 20% recency + 10% forks
5. **Composite score** uses formula: trust×0.40 + non-redundancy×0.30 + value×0.30

## When Adding a New Tool

1. Add the function to `server.py` with `@server.tool()` decorator
2. Add descriptive docstring (used as tool description for LLMs)
3. Add to the tool list in the module docstring
4. Update `SKILL.md` and `README.md`

## When Adding a New Capability Category

1. Add the category to `data/capabilities.json` with keywords, patterns, and examples
2. If needed, add a new value classification entry in `capabilities.py`
3. Run the test suite to verify no false positives/negatives

## Testing

```bash
# List all registered tools
python -c "
import asyncio
from mcp_manager.server import server
async def main():
    tools = await server.list_tools()
    for t in sorted(tools, key=lambda x: x.name):
        print(f'{t.name}')
asyncio.run(main())
"

# Test redundancy detection
python -c "
from mcp_manager.utils.capabilities import compute_redundancy
result = compute_redundancy('io.github.example/server', 'description')
print(result)
"
```

## Common Tasks

### Add a new value classification
Edit `VALUE_CLASSIFICATION` list in `src/mcp_manager/utils/capabilities.py`:
```python
{
    "value_type": "my_category",
    "value_score": 80,
    "label": "My Category",
    "keywords": ["keyword1", "keyword2"],
}
```

### Add a known redundant MCP server
Add to the `redundant_examples` list in the appropriate category in `data/capabilities.json`.

## 🔴 Do NOT

- Do NOT hardcode GitHub tokens or any credentials
- Do NOT execute subprocesses — use `httpx` for all external calls
- Do NOT modify `.mcp.json` without explicit user confirmation (`dry_run=True` is the safe default)

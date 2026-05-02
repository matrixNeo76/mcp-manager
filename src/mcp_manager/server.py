"""
MCP Manager — MCP server for discovering, evaluating, and managing MCP servers.

Architecture:
  server.py          — Entry point (CLI + FastMCP server creation)
  tools/             — Tool modules, each registers tools on the server
  utils/             — Core utilities (config, github, registry, capabilities)
  data/              — Static data files (capabilities.json)
"""

import argparse

from mcp.server.fastmcp import FastMCP

from mcp_manager import __version__

# ---------------------------------------------------------------------------
# Create FastMCP server (shared across all tool modules)
# ---------------------------------------------------------------------------
server = FastMCP(
    name="mcp-manager",
    instructions="Discover, evaluate, and manage MCP servers from the official registry. "
    "Use me to inspect local MCP config, search the registry, evaluate trust, "
    "and recommend additions. I understand which capabilities pi has built-in "
    "so I can filter out redundant MCP servers.",
)

# ---------------------------------------------------------------------------
# Register all tool modules
# ---------------------------------------------------------------------------
from mcp_manager.tools import (
    local_tools,
    trust_tools,
    info_tools,
    config_tools,
    search_tools,
    audit_tools,
)

local_tools.register(server)
trust_tools.register(server)
info_tools.register(server)
config_tools.register(server)
search_tools.register(server)
audit_tools.register(server)


# ============================ MAIN ===========================================


def main() -> None:
    """Entry point for mcp-manager."""
    parser = argparse.ArgumentParser(
        prog="mcp-manager",
        description="MCP Manager — discover, evaluate, and manage MCP servers",
    )
    parser.add_argument(
        "--version", action="version",
        version=f"mcp-manager v{__version__}",
    )
    parser.add_argument(
        "--http", action="store_true",
        help="Run as SSE HTTP server (experimental — requires uvicorn)",
    )
    parser.add_argument(
        "--port", metavar="PORT", type=int, default=8000,
        help="HTTP port (default: 8000)",
    )
    parser.add_argument(
        "--host", metavar="HOST", type=str, default="127.0.0.1",
        help="HTTP host (default: 127.0.0.1)",
    )
    args = parser.parse_args()

    if args.http:
        print("HTTP mode requires additional setup — use stdio mode or a proxy.")
        print(f"  python -m mcp_manager  # stdio mode (default)")
        parser.exit(1)
    else:
        server.run()


if __name__ == "__main__":
    main()

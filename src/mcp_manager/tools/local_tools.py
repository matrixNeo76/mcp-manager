"""Tool: list_local_servers — installed MCP servers from .mcp.json."""

from mcp.server.fastmcp import FastMCP
from mcp_manager.utils.config import list_local_servers as _list


def register(server: FastMCP) -> None:
    @server.tool(
        name="list_local_servers",
        description="List all MCP servers currently configured in the local .mcp.json file. "
        "Returns name, command, args, working directory, and environment variables for each server.",
    )
    async def list_local() -> list[dict]:
        """Reads .mcp.json from the current working directory."""
        return _list()

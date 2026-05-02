"""Tools: get_server_details, registry_health."""

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp_manager.utils.registry import get_server_detail, registry_health as check_health


def register(server: FastMCP) -> None:
    @server.tool(
        name="get_server_details",
        description="Get detailed information about a specific MCP server from the registry. "
        "Includes packages, repository info, transports, and status. "
        "Use the 'name' field returned by search_registry (e.g. 'io.github.user/my-server').",
    )
    async def server_details(server_name: str) -> dict[str, Any]:
        """Get detailed info about a specific server version from the registry."""
        return get_server_detail(server_name)

    @server.tool(
        name="registry_health",
        description="Check the health and status of the MCP Registry at registry.modelcontextprotocol.io. "
        "Returns reachability, response time, server count, and API version.",
    )
    async def health_check() -> dict[str, Any]:
        """Check if the MCP Registry is reachable and healthy."""
        return check_health()

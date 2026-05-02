"""Tool: generate_mcp_config — generate .mcp.json entry from registry metadata."""

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp_manager.utils.config import write_mcp_config_entry as _write_entry
from mcp_manager.utils.registry import get_server_detail


def register(server: FastMCP) -> None:
    @server.tool(
        name="generate_mcp_config",
        description="Generate a configuration block for adding a registry server to .mcp.json. "
        "By default returns a dry-run diff (no file changes). "
        "Set dry_run=False to actually write the configuration.",
    )
    async def gen_config(
        server_name: str,
        server_label: str = "",
        dry_run: bool = True,
        prefer_remote: bool = False,
    ) -> dict[str, Any]:
        """Generate an .mcp.json entry from a registry server's metadata."""
        detail = get_server_detail(server_name)
        if not detail.get("found"):
            return {"error": detail.get("error", f"Server {server_name} not found")}

        label = server_label or detail.get("name", "").split("/")[-1] or detail.get("name", "")

        packages = detail.get("packages", [])
        remotes = detail.get("remotes", [])
        has_both = bool(packages and remotes)

        # prefer_remote mode
        if prefer_remote and remotes:
            entry = {
                "url": remotes[0].get("url", ""),
                "type": remotes[0].get("type", "streamable-http"),
            }
            result = _write_entry(server_name=label, entry=entry, dry_run=dry_run)
            if isinstance(result, dict):
                result["also_available_as_package"] = has_both
            return result

        # Package mode
        if packages:
            stdio_pkg = next(
                (p for p in packages if p.get("transport_type") == "stdio"),
                packages[0],
            )
            transport = stdio_pkg.get("transport_type", "stdio")

            if transport == "stdio":
                entry = _build_stdio_entry(stdio_pkg)
            else:
                entry = {
                    "command": "npx",
                    "args": ["-y", stdio_pkg.get("identifier", "")],
                }

            # Environment variables from package
            env_vars = stdio_pkg.get("environment_variables", [])
            if env_vars:
                entry["env"] = {
                    ev["name"]: "${" + ev["name"] + "}"
                    for ev in env_vars
                    if isinstance(ev, dict) and ev.get("name")
                }
            else:
                entry["env"] = {}
        elif remotes:
            entry = {
                "url": remotes[0].get("url", ""),
                "type": remotes[0].get("type", "streamable-http"),
            }
        else:
            return {"error": "No packages or remotes found for this server"}

        result = _write_entry(server_name=label, entry=entry, dry_run=dry_run)
        if isinstance(result, dict) and has_both:
            result["also_available_as_remote"] = True
        return result


def _build_stdio_entry(pkg: dict) -> dict[str, Any]:
    """Build a stdio config entry from a package definition."""
    registry_type = pkg.get("registry_type", "npm")
    identifier = pkg.get("identifier", "")
    version = pkg.get("version", "")

    if registry_type == "npm":
        return {
            "command": "npx",
            "args": ["-y", identifier] if not version else ["-y", f"{identifier}@{version}"],
        }
    elif registry_type == "pypi":
        return {
            "command": "uvx" if version else "python",
            "args": [f"{identifier}=={version}"] if version else ["-m", identifier.replace("-", "_")],
        }
    elif registry_type == "oci":
        return {"command": "docker", "args": ["run", "-i", "--rm", identifier]}
    elif registry_type == "nuget":
        return {"command": "dotnet", "args": ["tool", "run", "--global", identifier]}
    elif registry_type == "mcpb":
        return {"command": identifier, "args": []}
    else:
        return {"command": "npx", "args": ["-y", identifier]}

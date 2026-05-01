"""
MCP Manager — MCP server for discovering, evaluating, and managing MCP servers.

Tools:
  list_local_servers      — Installed servers from .mcp.json
  search_registry         — Search the official MCP Registry
  get_server_details      — Detailed info about a registry server
  assess_trustworthiness  — Evaluate a GitHub repo's trust score
  search_with_trust       — Search + trust evaluation combined
  compare_alternatives    — Compare multiple servers for a task
  audit_workspace_mcp     — Full audit of local MCP setup
  generate_mcp_config     — Generate .mcp.json entry from a registry server
  registry_health         — Health check of the MCP Registry
"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_manager.utils.config import list_local_servers, write_mcp_config_entry
from mcp_manager.utils.github import fetch_repo_info, compute_trust_score
from mcp_manager.utils.registry import (
    list_servers as registry_list,
    get_server_detail,
    registry_health as check_health,
)

# ---------------------------------------------------------------------------
# Create FastMCP server
# ---------------------------------------------------------------------------
server = FastMCP(
    name="mcp-manager",
    instructions="Discover, evaluate, and manage MCP servers from the official registry. "
    "Use me to inspect local MCP config, search the registry, evaluate trust, and recommend additions.",
)


# ============================ MICROFASE 2 ===================================

@server.tool(
    name="list_local_servers",
    description="List all MCP servers currently configured in the local .mcp.json file. "
    "Returns name, command, args, working directory, and environment variables for each server.",
)
async def list_local() -> list[dict[str, Any]]:
    """Reads .mcp.json from the current working directory."""
    return list_local_servers()


# ============================ MICROFASE 3 ===================================

@server.tool(
    name="search_registry",
    description="Search for MCP servers on the official registry (registry.modelcontextprotocol.io). "
    "Supports substring search on server names, pagination, and version filtering.",
)
async def search_registry(
    query: str,
    limit: int = 20,
    version: str = "latest",
) -> list[dict[str, Any]]:
    """Search for MCP servers on the official registry."""
    return registry_list(search=query, limit=limit, version=version)


# ============================ MICROFASE 4 ===================================

@server.tool(
    name="get_server_details",
    description="Get detailed information about a specific MCP server from the registry. "
    "Includes packages, repository info, transports, and status. "
    "Use the 'name' field returned by search_registry (e.g. 'io.github.user/my-server').",
)
async def server_details(server_name: str) -> dict[str, Any]:
    """Get detailed info about a specific server version from the registry."""
    return get_server_detail(server_name)


# ============================ MICROFASE 5 ===================================

@server.tool(
    name="assess_trustworthiness",
    description="Evaluate the trustworthiness of a GitHub repository linked to an MCP server. "
    "Checks stars, forks, recency of updates, and computes a trust score (0-100). "
    "Returns is_trusted (bool) and warnings if score is below threshold.",
)
async def trust_assessment(
    repository_url: str,
    min_stars: int = 10,
) -> dict[str, Any]:
    """Evaluate a GitHub repository and compute trust score."""
    repo_info = fetch_repo_info(repository_url)
    if not repo_info["found"]:
        return {
            "repository_url": repository_url,
            "trust_score": 0,
            "is_trusted": False,
            "warnings": [repo_info.get("error", "Repository not found")],
            "repo_info": repo_info,
        }

    score = compute_trust_score(repo_info, min_stars=min_stars)
    return {
        "repository_url": repository_url,
        "stars": repo_info["stars"],
        "forks": repo_info["forks"],
        "description": repo_info["description"],
        "last_push": repo_info["last_push"],
        "days_since_update": repo_info["days_since_update"],
        "language": repo_info["language"],
        **score,
    }


# ============================ MICROFASE 6 ===================================

@server.tool(
    name="search_with_trust",
    description="Search the MCP Registry AND evaluate trust for each result. "
    "Returns servers ranked by trust score, with GitHub stats. "
    "Servers without a GitHub repository get trust_score = 0.",
)
async def search_trusted(
    query: str,
    limit: int = 20,
    min_stars: int = 10,
    filter_untrusted: bool = False,
) -> list[dict[str, Any]]:
    """Search registry and evaluate trust for each result."""
    servers = registry_list(search=query, limit=limit, version="latest")

    results = []
    for sv in servers:
        entry: dict[str, Any] = {**sv}
        repo_url = sv.get("repository_url")
        if repo_url:
            repo_info = fetch_repo_info(repo_url)
            entry["repo_info"] = repo_info
            entry["stars"] = repo_info.get("stars", 0)
            entry["forks"] = repo_info.get("forks", 0)
            entry["days_since_update"] = repo_info.get("days_since_update", 9999)
            if repo_info["found"]:
                score = compute_trust_score(repo_info, min_stars=min_stars)
                entry["trust_score"] = score["trust_score"]
                entry["is_trusted"] = score["is_trusted"]
                entry["trust_warnings"] = score["warnings"]
            else:
                entry["trust_score"] = 0
                entry["is_trusted"] = False
                entry["trust_warnings"] = [repo_info.get("error", "Unknown error")]
        else:
            entry["trust_score"] = 0
            entry["is_trusted"] = False
            entry["trust_warnings"] = ["No GitHub repository URL in registry"]

        results.append(entry)

    # Sort by trust_score descending
    results.sort(key=lambda x: x.get("trust_score", 0), reverse=True)

    if filter_untrusted:
        results = [r for r in results if r.get("is_trusted", False)]

    return results


# ============================ MICROFASE 7 ===================================

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
) -> dict[str, Any]:
    """Generate an .mcp.json entry from a registry server's metadata."""
    detail = get_server_detail(server_name)
    if not detail.get("found"):
        return {"error": detail.get("error", f"Server {server_name} not found")}

    label = server_label or detail.get("name", "").split("/")[-1] or detail.get("name", "")

    # Try to build a config entry from packages or remotes
    packages = detail.get("packages", [])
    remotes = detail.get("remotes", [])

    if packages:
        # Prefer first stdio package
        stdio_pkg = next(
            (p for p in packages if p.get("transport_type") == "stdio"),
            packages[0],
        )
        transport = stdio_pkg.get("transport_type", "stdio")

        if transport == "stdio":
            registry_type = stdio_pkg.get("registry_type", "npm")
            identifier = stdio_pkg.get("identifier", "")
            version = stdio_pkg.get("version", "")

            if registry_type == "npm":
                entry: dict[str, Any] = {
                    "command": "npx",
                    "args": ["-y", identifier] if not version else ["-y", f"{identifier}@{version}"],
                }
            elif registry_type == "pypi":
                entry = {
                    "command": "uvx" if version else "python",
                    "args": [f"{identifier}=={version}"] if version else ["-m", identifier.replace("-", "_")],
                }
            else:
                entry = {
                    "command": "npx",
                    "args": ["-y", identifier],
                }

            # Add required environment variables from the package definition
            entry["env"] = {}
        else:
            # Streamable HTTP or SSE
            entry = {
                "command": "npx",
                "args": ["-y", stdio_pkg.get("identifier", "")],
            }
    elif remotes:
        # Remote server (streamable HTTP or SSE) — suggest URL-based config
        entry = {
            "url": remotes[0].get("url", ""),
            "type": remotes[0].get("type", "streamable-http"),
        }
    else:
        return {"error": "No packages or remotes found for this server"}

    return write_mcp_config_entry(
        server_name=label,
        entry=entry,
        dry_run=dry_run,
    )


# ============================ MICROFASE 8 ===================================

@server.tool(
    name="compare_alternatives",
    description="Search for alternative MCP servers and compare them side by side. "
    "Includes trust scores, GitHub stats, descriptions, and versions. "
    "Optionally include a local server name as baseline for comparison.",
)
async def compare_alternatives(
    query: str,
    local_server_name: str = "",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Find and compare alternative MCP servers for a given task."""
    results = await search_trusted(
        query=query, limit=limit, min_stars=5, filter_untrusted=False
    )

    # If a local server name is provided, try to find it in the list
    if local_server_name:
        local_match = None
        for r in results:
            if local_server_name.lower() in r.get("name", "").lower():
                local_match = r
                break
        if local_match:
            local_match["is_current"] = True

    return results


# ============================ MICROFASE 9 ===================================

@server.tool(
    name="audit_workspace_mcp",
    description="Perform a comprehensive audit of the local MCP configuration. "
    "Checks each installed server against the registry, evaluates trust scores, "
    "detects outdated versions, and provides actionable recommendations.",
)
async def audit_workspace() -> dict[str, Any]:
    """Full audit of local MCP servers vs registry."""
    local = list_local_servers()
    if not local:
        return {
            "installed_count": 0,
            "message": "No MCP servers configured. Use search_registry to find servers to add.",
        }

    registry_health = check_health()
    checked = []
    for sv in local:
        name = sv["name"]
        entry = {
            "local_name": name,
            "command": sv.get("command", ""),
            "registry_match": None,
            "registry_version": None,
            "is_outdated": False,
            "trust_score": None,
            "is_trusted": None,
            "warnings": [],
        }

        # Search registry by name
        registry_results = registry_list(search=name, limit=3, version="latest")
        match = None
        for r in registry_results:
            if name.lower() in r.get("name", "").lower():
                match = r
                break

        if match:
            entry["registry_match"] = match["name"]
            entry["registry_version"] = match["version"]
            entry["is_outdated"] = False  # We can't reliably compare versions

            # Trust evaluation
            repo_url = match.get("repository_url")
            if repo_url:
                repo_info = fetch_repo_info(repo_url)
                if repo_info["found"]:
                    score = compute_trust_score(repo_info)
                    entry["trust_score"] = score["trust_score"]
                    entry["is_trusted"] = score["is_trusted"]
                    if score["warnings"]:
                        entry["warnings"].extend(score["warnings"])
        else:
            entry["warnings"].append("Not found in the MCP Registry")

        checked.append(entry)

    trusted = sum(1 for c in checked if c.get("is_trusted"))
    untrusted = sum(1 for c in checked if c.get("is_trusted") is False)

    return {
        "registry_reachable": registry_health.get("reachable", False),
        "registry_servers_count": registry_health.get("servers_count", 0),
        "installed_count": len(local),
        "trusted_count": trusted,
        "untrusted_count": untrusted,
        "servers": checked,
        "recommendations": _generate_recommendations(checked),
    }


def _generate_recommendations(checked: list[dict]) -> list[str]:
    """Generate actionable recommendations from audit results."""
    recs = []
    for c in checked:
        if c.get("is_trusted") is False:
            recs.append(
                f"⚠️  '{c['local_name']}' has low trust score ({c.get('trust_score', 0)}). "
                "Consider replacing with a more established alternative."
            )
        if not c.get("registry_match"):
            recs.append(
                f"🔍 '{c['local_name']}' was not found in the MCP Registry. "
                "It may be unpublished or use a custom name."
            )
    if not recs:
        recs.append("✅ All installed servers look good!")
    return recs


# ============================ MICROFASE 10 ==================================

@server.tool(
    name="registry_health",
    description="Check the health and status of the MCP Registry at registry.modelcontextprotocol.io. "
    "Returns reachability, response time, server count, and API version.",
)
async def health_check() -> dict[str, Any]:
    """Check if the MCP Registry is reachable and healthy."""
    return check_health()


# ============================ MAIN ===========================================


def main() -> None:
    """Entry point for mcp-manager."""
    server.run()


if __name__ == "__main__":
    main()

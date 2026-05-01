"""MCP Registry API client (registry.modelcontextprotocol.io)."""

from typing import Any

import httpx

import os

REGISTRY_BASE = "https://registry.modelcontextprotocol.io"
REGISTRY_API_VERSION = os.environ.get("REGISTRY_API_VERSION", "v0.1")
REGISTRY_API = f"{REGISTRY_BASE}/{REGISTRY_API_VERSION}"
REGISTRY_TIMEOUT = int(os.environ.get("REGISTRY_TIMEOUT", "30"))


def list_servers(
    search: str | None = None,
    limit: int = 20,
    version: str = "latest",
    updated_since: str | None = None,
) -> list[dict[str, Any]]:
    """List servers from the MCP Registry with pagination.

    Returns a flat list of server entries with registry metadata.
    """
    servers: list[dict[str, Any]] = []
    cursor: str | None = None

    with httpx.Client(timeout=REGISTRY_TIMEOUT) as client:
        while len(servers) < limit:
            params: dict[str, Any] = {
                "limit": min(100, limit - len(servers)),
                "version": version,
            }
            if search:
                params["search"] = search
            if cursor:
                params["cursor"] = cursor
            if updated_since:
                params["updated_since"] = updated_since

            resp = client.get(f"{REGISTRY_API}/servers", params=params)

            if resp.status_code == 429:
                raise RuntimeError("Registry rate limit exceeded. Try again later.")
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Registry returned {resp.status_code}: {resp.text[:200]}"
                )

            data = resp.json()
            batch = data.get("servers") or []
            for entry in batch:
                if isinstance(entry, dict) and "server" in entry:
                    server_data = entry["server"]
                    meta = entry.get("_meta", {})
                    registry_meta = meta.get(
                        "io.modelcontextprotocol.registry/official", {}
                    )
                    servers.append({
                        "name": server_data.get("name", ""),
                        "title": server_data.get("title"),
                        "description": server_data.get("description", ""),
                        "version": server_data.get("version", ""),
                        "repository_url": (
                            server_data.get("repository", {}).get("url")
                            if isinstance(server_data.get("repository"), dict)
                            else None
                        ),
                        "repository_source": (
                            server_data.get("repository", {}).get("source")
                            if isinstance(server_data.get("repository"), dict)
                            else None
                        ),
                        "repository_id": (
                            server_data.get("repository", {}).get("id")
                            if isinstance(server_data.get("repository"), dict)
                            else None
                        ),
                        "website_url": server_data.get("websiteUrl"),
                        "status": registry_meta.get("status", "unknown"),
                        "is_latest": registry_meta.get("isLatest", False),
                        "published_at": registry_meta.get("publishedAt"),
                        "updated_at": registry_meta.get("updatedAt"),
                    })

            meta = data.get("metadata", {})
            cursor = meta.get("nextCursor")
            if not cursor:
                break

    return servers[:limit]


def get_server_detail(server_name: str) -> dict[str, Any]:
    """Get detailed information about the latest version of a server.

    server_name should be URL-encoded (e.g., 'io.github.user%2Fmy-server').
    """
    import re
    import urllib.parse

    # Validate server name: only alphanumeric, dots, hyphens, slashes, underscores, colons
    if not re.match(r'^[a-zA-Z0-9._\-/:]+$', server_name):
        return {
            "found": False,
            "error": f"Invalid server name '{server_name}'. "
            "Expected format: 'namespace/server-name' (alphanumeric, dots, hyphens).",
        }

    encoded = urllib.parse.quote(server_name, safe="")
    # If the name already contains %2F, don't double-encode
    if "%2F" in server_name or "%2f" in server_name:
        encoded = server_name

    url = f"{REGISTRY_API}/servers/{encoded}/versions/latest"

    with httpx.Client(timeout=REGISTRY_TIMEOUT) as client:
        resp = client.get(url)

    if resp.status_code == 404:
        return {"found": False, "error": f"Server '{server_name}' not found"}
    if resp.status_code != 200:
        return {
            "found": False,
            "error": f"Registry returned {resp.status_code}: {resp.text[:200]}",
        }

    data = resp.json()
    server_data = data.get("server", data) if isinstance(data, dict) else {}

    meta = {}
    if isinstance(data, dict):
        resp_meta = data.get("_meta", {})
        meta = resp_meta.get("io.modelcontextprotocol.registry/official", {})

    detail = {
        "found": True,
        "name": server_data.get("name", ""),
        "title": server_data.get("title"),
        "description": server_data.get("description", ""),
        "version": server_data.get("version", ""),
        "website_url": server_data.get("websiteUrl"),
        "status": meta.get("status", "unknown"),
        "is_latest": meta.get("isLatest", False),
        "published_at": meta.get("publishedAt"),
        "updated_at": meta.get("updatedAt"),
    }

    # Repository info
    repo = server_data.get("repository")
    if isinstance(repo, dict):
        detail["repository"] = {
            "url": repo.get("url"),
            "source": repo.get("source"),
            "id": repo.get("id"),
            "subfolder": repo.get("subfolder"),
        }

    # Packages
    packages = server_data.get("packages")
    if isinstance(packages, list):
        detail["packages"] = [
            {
                "registry_type": p.get("registryType"),
                "identifier": p.get("identifier"),
                "version": p.get("version"),
                "transport_type": p.get("transport", {}).get("type"),
                "transport_url": p.get("transport", {}).get("url"),
                "environment_variables": p.get("environmentVariables", []),
            }
            for p in packages
            if isinstance(p, dict)
        ]

    # Remotes
    remotes = server_data.get("remotes")
    if isinstance(remotes, list):
        detail["remotes"] = [
            {"type": r.get("type"), "url": r.get("url")}
            for r in remotes
            if isinstance(r, dict)
        ]

    # Icons
    icons = server_data.get("icons")
    if isinstance(icons, list):
        detail["icons"] = icons

    return detail


def registry_health() -> dict[str, Any]:
    """Check the health of the MCP Registry."""
    import time

    start = time.time()
    try:
        with httpx.Client(timeout=REGISTRY_TIMEOUT) as client:
            health_resp = client.get(f"{REGISTRY_BASE}/v0.1/health")
            version_resp = client.get(f"{REGISTRY_BASE}/v0.1/version")
            count_resp = client.get(
                f"{REGISTRY_API}/servers?limit=1&version=latest"
            )
        elapsed_ms = round((time.time() - start) * 1000)

        count = 0
        if count_resp.status_code == 200:
            meta = count_resp.json().get("metadata", {})
            count = meta.get("count", 0)

        api_version = ""
        if version_resp.status_code == 200:
            vdata = version_resp.json()
            api_version = vdata.get("version", "")

        return {
            "reachable": health_resp.status_code == 200,
            "servers_count": count,
            "response_time_ms": elapsed_ms,
            "api_version": api_version,
        }
    except Exception as e:
        return {
            "reachable": False,
            "servers_count": 0,
            "response_time_ms": 0,
            "api_version": "",
            "error": str(e),
        }

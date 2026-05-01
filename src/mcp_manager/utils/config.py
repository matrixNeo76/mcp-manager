"""Read and write MCP configuration files (.mcp.json)."""

import json
import os
from pathlib import Path
from typing import Any


def find_mcp_config(path: str | None = None) -> Path:
    """Find the .mcp.json file. Returns path or raises FileNotFoundError."""
    env_path = os.environ.get("MCP_CONFIG_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists() and p.is_file():
            return p
        raise FileNotFoundError(
            f"MCP_CONFIG_PATH={env_path} — file not found. "
            "Check the path or unset the variable to search from CWD."
        )

    search_start = Path(path).resolve() if path else Path.cwd().resolve()
    # Search upward from the given directory
    for parent in [search_start] + list(search_start.parents):
        candidate = parent / ".mcp.json"
        if candidate.exists() and candidate.is_file():
            return candidate

    raise FileNotFoundError(
        f"No .mcp.json found from {search_start} upward. "
        "Set MCP_CONFIG_PATH env var or run from a project with .mcp.json."
    )


def read_mcp_config(path: str | None = None) -> dict[str, Any]:
    """Read and return the mcpServers dict from .mcp.json."""
    config_path = find_mcp_config(path)
    try:
        raw = config_path.read_text(encoding="utf-8")
        data: dict = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Malformed .mcp.json at {config_path}: {e}"
        ) from e

    servers = data.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError(
            f"Expected 'mcpServers' to be an object, got {type(servers).__name__}"
        )
    return servers


def list_local_servers(path: str | None = None) -> list[dict[str, Any]]:
    """Return a list of installed MCP servers with their details."""
    try:
        servers = read_mcp_config(path)
    except FileNotFoundError:
        return []

    result = []
    for name, config in servers.items():
        if not isinstance(config, dict):
            continue
        result.append({
            "name": name,
            "command": config.get("command", ""),
            "args": config.get("args", []),
            "cwd": config.get("cwd"),
            "env": dict(config.get("env", {})),
        })
    return result


def write_mcp_config_entry(
    server_name: str,
    entry: dict[str, Any],
    path: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Add or update a server entry in .mcp.json.

    If dry_run=True (default), return the diff without writing.
    If dry_run=False, write to disk.
    """
    try:
        config_path = find_mcp_config(path)
    except FileNotFoundError:
        raise FileNotFoundError(
            "Cannot write config: no .mcp.json found. "
            "Run from a project directory containing .mcp.json "
            "or set the MCP_CONFIG_PATH environment variable."
        )
    raw = config_path.read_text(encoding="utf-8")
    data: dict = json.loads(raw)

    if "mcpServers" not in data:
        data["mcpServers"] = {}

    old_entry = data["mcpServers"].get(server_name)
    data["mcpServers"][server_name] = entry

    if dry_run:
        return {
            "config_path": str(config_path),
            "server_name": server_name,
            "operation": "update" if old_entry else "create",
            "old_entry": old_entry,
            "new_entry": entry,
        }

    config_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return {
        "config_path": str(config_path),
        "server_name": server_name,
        "operation": "updated" if old_entry else "created",
    }

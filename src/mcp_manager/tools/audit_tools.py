"""Tools: audit_workspace_mcp, compare_alternatives, pi_capabilities."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_manager.utils.capabilities import (
    compute_redundancy,
    classify_value,
    compute_composite_score,
    get_redundancy_help,
)
from mcp_manager.utils.config import list_local_servers
from mcp_manager.utils.github import fetch_repo_info, compute_trust_score
from mcp_manager.utils.registry import list_servers as registry_list, registry_health as check_health

from mcp_manager.tools.search_tools import _enrich_with_scores


def register(server: FastMCP) -> None:
    @server.tool(
        name="compare_alternatives",
        description="Search for alternative MCP servers and compare them side by side. "
        "Includes trust scores, redundancy check, value classification, composite score. "
        "Optionally include a local server name as baseline for comparison.",
    )
    async def compare_alternatives(
        query: str,
        local_server_name: str = "",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Find and compare alternative MCP servers for a given task."""
        servers = registry_list(search=query, limit=limit, version="latest")
        enriched = await _enrich_with_scores(servers, min_stars=5, filter_untrusted=False)

        if local_server_name:
            for r in enriched:
                if local_server_name.lower() in r.get("name", "").lower():
                    r["is_current"] = True
                    break

        return enriched

    @server.tool(
        name="audit_workspace_mcp",
        description="Perform a comprehensive audit of the local MCP configuration. "
        "Checks each installed server against the registry, evaluates trust scores, "
        "detects redundant servers (duplicating pi built-ins), "
        "and provides actionable recommendations.",
    )
    async def audit_workspace() -> dict[str, Any]:
        """Full audit of local MCP servers vs registry + pi built-in capabilities."""
        local = list_local_servers()
        if not local:
            return {
                "installed_count": 0,
                "message": "No MCP servers configured. Use search_registry to find servers to add.",
            }

        health = check_health()
        checked = []
        for sv in local:
            name = sv["name"]
            entry: dict[str, Any] = {
                "local_name": name,
                "command": sv.get("command", ""),
                "registry_match": None,
                "registry_version": None,
                "is_outdated": False,
                "trust_score": None,
                "is_trusted": None,
                "redundant": False,
                "redundant_reason": None,
                "value_label": "[Gen] Generico",
                "composite_score": None,
                "warnings": [],
            }

            # 1) Check registry
            registry_results = registry_list(search=name, limit=10, version="latest")
            match = None
            for r in registry_results:
                if name.lower() in r.get("name", "").lower():
                    match = r
                    break

            if match:
                entry["registry_match"] = match["name"]
                entry["registry_version"] = match["version"]

                # 2) Redundancy check
                red = compute_redundancy(match["name"], match.get("description", ""))
                entry["redundant"] = red["redundant"]
                entry["redundant_reason"] = red["redundant_reason"]
                if red["redundant"]:
                    entry["warnings"].append(f"[RED] RIDONDANTE: {red['redundant_reason']}")

                # 3) Value classification
                val = classify_value(match["name"], match.get("description", ""))
                entry["value_label"] = val["value_label"]
                entry["value_score"] = val["value_score"]

                # 4) Trust evaluation
                repo_url = match.get("repository_url")
                if repo_url:
                    repo_info = fetch_repo_info(repo_url)
                    if repo_info["found"]:
                        score = compute_trust_score(repo_info)
                        entry["trust_score"] = score["trust_score"]
                        entry["is_trusted"] = score["is_trusted"]
                        entry["composite_score"] = compute_composite_score(
                            trust_score=score["trust_score"],
                            redundancy_score=red["redundancy_score"],
                            value_score=val["value_score"],
                        )
                        if score["warnings"]:
                            entry["warnings"].extend(score["warnings"])
            else:
                entry["warnings"].append("Not found in the MCP Registry")

            checked.append(entry)

        trusted = sum(1 for c in checked if c.get("is_trusted"))
        untrusted = sum(1 for c in checked if c.get("is_trusted") is False)
        redundant = sum(1 for c in checked if c.get("redundant"))

        return {
            "registry_reachable": health.get("reachable", False),
            "registry_servers_count": health.get("servers_count", 0),
            "installed_count": len(local),
            "trusted_count": trusted,
            "untrusted_count": untrusted,
            "redundant_count": redundant,
            "redundant_servers": [c["local_name"] for c in checked if c.get("redundant")],
            "servers": checked,
            "recommendations": _generate_recommendations(checked),
        }

    @server.tool(
        name="pi_capabilities",
        description="Mostra le capacita built-in di pi/Craft Agents. "
        "Utile per capire quali MCP server sono RIDONDANTI (gia presenti in pi) "
        "e quali invece aggiungono valore come integrazioni esterne.",
    )
    async def pi_caps() -> str:
        """Return markdown summary of pi built-in capabilities."""
        return get_redundancy_help()


def _generate_recommendations(checked: list[dict]) -> list[str]:
    """Generate actionable recommendations from audit results."""
    recs = []
    for c in checked:
        if c.get("redundant"):
            recs.append(
                f"[RED] '{c['local_name']}' e RIDONDANTE: {c['redundant_reason']}. Puoi rimuoverlo."
            )
        if c.get("is_trusted") is False and c.get("trust_score") is not None:
            recs.append(
                f"[WARN] '{c['local_name']}' ha trust score basso ({c.get('trust_score', 0)}). "
                "Considera una alternativa piu affidabile."
            )
        if not c.get("registry_match"):
            recs.append(
                f"[INFO] '{c['local_name']}' non trovato nel Registry MCP. "
                "Potrebbe non essere pubblicato o avere un nome diverso."
            )
    if not recs:
        recs.append("[OK] Tutti i server installati sono ok!")
    return recs

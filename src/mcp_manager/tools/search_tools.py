"""Tools: search_registry, search_with_trust, search_useful_mcp."""

import asyncio
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_manager.utils.capabilities import (
    compute_redundancy,
    classify_value,
    compute_composite_score,
)
from mcp_manager.utils.github import fetch_repo_info, compute_trust_score, get_rate_limit_status
from mcp_manager.utils.registry import list_servers as registry_list


def register(server: FastMCP) -> None:
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

    @server.tool(
        name="search_with_trust",
        description="Search the MCP Registry AND evaluate trust for each result. "
        "Returns servers ranked by trust score, with GitHub stats. "
        "Servers without a GitHub repository get trust_score = 0. "
        "Also includes redundancy and composite scores.",
    )
    async def search_trusted(
        query: str,
        limit: int = 20,
        min_stars: int = 10,
        filter_untrusted: bool = False,
    ) -> list[dict[str, Any]]:
        """Search registry and evaluate trust + redundancy for each result."""
        servers = registry_list(search=query, limit=limit, version="latest")
        return await _enrich_with_scores(servers, min_stars, filter_untrusted)

    @server.tool(
        name="search_useful_mcp",
        description="Cerca MCP server che aggiungono VALORE REALE a pi/Craft Agents, "
        "escludendo automaticamente quelli ridondanti (filesystem, browser, shell, search...). "
        "Ogni risultato include: trust score, redundancy check, value classification, "
        "e composite score per un ranking intelligente.",
    )
    async def search_useful(
        query: str,
        limit: int = 20,
        min_stars: int = 10,
        filter_untrusted: bool = True,
        include_redundant: bool = False,
    ) -> list[dict[str, Any]]:
        """Search for MCP servers that add real value beyond pi's built-in capabilities."""
        servers = registry_list(search=query, limit=limit, version="latest")
        enriched = await _enrich_with_scores(servers, min_stars, filter_untrusted)

        if not include_redundant:
            enriched = [e for e in enriched if not e.get("redundant", False)]

        return enriched


async def _enrich_with_scores(
    servers: list[dict],
    min_stars: int = 10,
    filter_untrusted: bool = False,
) -> list[dict[str, Any]]:
    """Enrich registry servers with trust, redundancy, value, and composite scores.

    Trust evaluation runs in parallel via asyncio.gather (max 5 concurrent).
    """
    # Phase 1: compute redundancy + value (synchronous, no network)
    for sv in servers:
        name = sv.get("name", "")
        desc = sv.get("description", "")
        redundancy = compute_redundancy(name, desc)
        value = classify_value(name, desc)
        sv["_redundancy"] = redundancy
        sv["_value"] = value

    # Phase 2: fetch trust info in parallel (network-bound)
    sem = asyncio.Semaphore(5)

    async def _fetch_trust(sv: dict) -> dict:
        async with sem:
            repo_url = sv.get("repository_url")
            if not repo_url:
                return {
                    "trust_score": 0, "is_trusted": False,
                    "trust_warnings": ["No GitHub repository URL in registry"],
                    "stars": 0, "forks": 0, "days_since_update": 9999,
                }
            loop = asyncio.get_event_loop()
            repo_info = await loop.run_in_executor(None, fetch_repo_info, repo_url)
            result = {"repo_info": repo_info}
            result["stars"] = repo_info.get("stars", 0)
            result["forks"] = repo_info.get("forks", 0)
            result["days_since_update"] = repo_info.get("days_since_update", 9999)
            if repo_info["found"]:
                score = compute_trust_score(repo_info, min_stars=min_stars)
                result["trust_score"] = score["trust_score"]
                result["is_trusted"] = score["is_trusted"]
                result["trust_warnings"] = score["warnings"]
            else:
                result["trust_score"] = 0
                result["is_trusted"] = False
                result["trust_warnings"] = [repo_info.get("error", "Unknown error")]
            return result

    trust_results = await asyncio.gather(*[_fetch_trust(sv) for sv in servers])

    # Phase 3: combine everything into final entries
    results = []
    for sv, trust in zip(servers, trust_results):
        redundancy = sv["_redundancy"]
        value = sv["_value"]

        entry: dict[str, Any] = {
            "name": sv.get("name", ""),
            "title": sv.get("title"),
            "description": sv.get("description", ""),
            "version": sv.get("version", ""),
            "repository_url": sv.get("repository_url"),
            "status": sv.get("status", "unknown"),
            **trust,
            "redundancy_score": redundancy["redundancy_score"],
            "redundant": redundancy["redundant"],
            "redundant_category": redundancy["redundant_category"],
            "redundant_reason": redundancy["redundant_reason"],
            "value_type": value["value_type"],
            "value_score": value["value_score"],
            "value_label": value["value_label"],
            "value_match_confidence": value["value_match_confidence"],
        }

        entry["composite_score"] = compute_composite_score(
            trust_score=entry["trust_score"],
            redundancy_score=redundancy["redundancy_score"],
            value_score=value["value_score"],
        )

        results.append(entry)

    # Attach rate limit warning if low
    rl = get_rate_limit_status()
    if rl["is_low"]:
        _attach_rate_warning(results, rl)

    results.sort(key=lambda x: x.get("composite_score", 0), reverse=True)

    if filter_untrusted:
        results = [r for r in results if r.get("is_trusted", False)]

    return results


def _attach_rate_warning(results: list[dict], rl: dict) -> None:
    """Attach a rate limit warning to the first result's warnings."""
    if not results:
        return
    reset_min = rl.get("resets_in_minutes")
    reset_part = f" Resetta tra ~{reset_min}min." if reset_min else ""
    msg = (
        f" GitHub API rate limit basso: {rl.get('remaining', '?')}/{rl.get('limit', '?')} richieste.{reset_part} "
        "Imposta GITHUB_TOKEN per 5.000 req/h."
    )
    warnings = results[0].setdefault("trust_warnings", [])
    if msg not in warnings:
        warnings.insert(0, msg)

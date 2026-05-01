"""
MCP Manager — MCP server for discovering, evaluating, and managing MCP servers.

Tools:
 list_local_servers   — Installed servers from .mcp.json
 search_registry     — Search the official MCP Registry
 get_server_details   — Detailed info about a registry server
 assess_trustworthiness — Evaluate a GitHub repo's trust score
 search_with_trust    — Search + trust evaluation combined
 search_useful_mcp    — [NEW] Search + trust + redundancy filter + value classification
 compare_alternatives  — Compare multiple servers for a task
 audit_workspace_mcp   — Full audit of local MCP setup
 generate_mcp_config   — Generate .mcp.json entry from a registry server
 registry_health     — Health check of the MCP Registry
"""

import asyncio
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_manager.utils.capabilities import (
  compute_redundancy,
  classify_value,
  compute_composite_score,
  get_redundancy_help,
)
from mcp_manager.utils.config import list_local_servers, write_mcp_config_entry
from mcp_manager.utils.github import fetch_repo_info, compute_trust_score, get_rate_limit_status
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
  "Use me to inspect local MCP config, search the registry, evaluate trust, "
  "and recommend additions. I understand which capabilities pi has built-in "
  "so I can filter out redundant MCP servers.",
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


# ============================ MICROFASE 6 (aggiornata) ======================

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


async def _enrich_with_scores(
  servers: list[dict],
  min_stars: int = 10,
  filter_untrusted: bool = False,
) -> list[dict[str, Any]]:
  """Enrich registry servers with trust, redundancy, value, and composite scores.

  Trust evaluation runs in parallel via asyncio.gather (max 5 concurrent)
  to minimize GitHub API latency.
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
  sem = asyncio.Semaphore(5) # max 5 concurrent requests

  async def _fetch_trust(sv: dict) -> dict:
    async with sem:
      repo_url = sv.get("repository_url")
      if not repo_url:
        return {"trust_score": 0, "is_trusted": False, "trust_warnings": ["No GitHub repository URL in registry"],
            "stars": 0, "forks": 0, "days_since_update": 9999}
      # fetch_repo_info is sync — run in executor to avoid blocking
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

  # Sort by composite_score descending
  results.sort(key=lambda x: x.get("composite_score", 0), reverse=True)

  if filter_untrusted:
    results = [r for r in results if r.get("is_trusted", False)]

  return results


def _attach_rate_warning(results: list[dict], rl: dict) -> None:
  """Attach a rate limit warning to the first result's warnings."""
  if not results:
    return
  msg = (
    f" GitHub API rate limit basso: {rl.get('remaining', '?')}/{rl.get('limit', '?')} richieste rimaste. "
    "Imposta GITHUB_TOKEN per 5.000 req/h."
  )
  warnings = results[0].setdefault("trust_warnings", [])
  if msg not in warnings:
    warnings.insert(0, msg)


# ============================ MICROFASE 5 (NEW) =============================

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
  has_both = bool(packages and remotes)

  # If prefer_remote and remotes available, use remote URL
  if prefer_remote and remotes:
    entry = {
      "url": remotes[0].get("url", ""),
      "type": remotes[0].get("type", "streamable-http"),
    }
    result = write_mcp_config_entry(server_name=label, entry=entry, dry_run=dry_run)
    if isinstance(result, dict):
      result["also_available_as_package"] = has_both
    return result

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
      elif registry_type == "oci":
        # OCI container images — run via docker/podman
        entry = {
          "command": "docker",
          "args": ["run", "-i", "--rm", identifier],
        }
      elif registry_type == "nuget":
        # .NET tools
        entry = {
          "command": "dotnet",
          "args": ["tool", "run", "--global", identifier],
        }
      elif registry_type == "mcpb":
        # MCP Bundle — download and execute directly
        entry = {
          "command": identifier, # URL or path to the bundle
          "args": [],
        }
      else:
        entry = {
          "command": "npx",
          "args": ["-y", identifier],
        }
      # Extract environment variables from package definition
      env_vars = stdio_pkg.get("environment_variables", [])
      if env_vars:
        entry["env"] = {
          ev["name"]: "${" + ev["name"] + "}" # placeholder for user to fill
          for ev in env_vars
          if isinstance(ev, dict) and ev.get("name")
        }
      else:
        entry["env"] = {}
    else:
      entry = {
        "command": "npx",
        "args": ["-y", stdio_pkg.get("identifier", "")],
      }
  elif remotes:
    entry = {
      "url": remotes[0].get("url", ""),
      "type": remotes[0].get("type", "streamable-http"),
    }
  else:
    return {"error": "No packages or remotes found for this server"}

  result = write_mcp_config_entry(
    server_name=label,
    entry=entry,
    dry_run=dry_run,
  )
  if isinstance(result, dict) and has_both:
    result["also_available_as_remote"] = True
  return result


# ============================ MICROFASE 8 (aggiornata) ======================

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
  results = await search_useful(
    query=query, limit=limit, min_stars=5, filter_untrusted=False, include_redundant=True
  )

  if local_server_name:
    for r in results:
      if local_server_name.lower() in r.get("name", "").lower():
        r["is_current"] = True
        break

  return results


# ============================ MICROFASE 9 (aggiornata) ======================

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
    entry = {
      "local_name": name,
      "command": sv.get("command", ""),
      "registry_match": None,
      "registry_version": None,
      "is_outdated": False,
      "trust_score": None,
      "is_trusted": None,
      "redundant": False,
      "redundant_reason": None,
      "value_label": " Generico",
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
        entry["warnings"].append(
          f" RIDONDANTE: {red['redundant_reason']}"
        )

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

          # 5) Composite score
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


def _generate_recommendations(checked: list[dict]) -> list[str]:
  """Generate actionable recommendations from audit results."""
  recs = []
  for c in checked:
    if c.get("redundant"):
      recs.append(
        f" '{c['local_name']}' è RIDONDANTE: {c['redundant_reason']}. "
        "Puoi rimuoverlo."
      )
    if c.get("is_trusted") is False:
      recs.append(
        f" '{c['local_name']}' ha trust score basso ({c.get('trust_score', 0)}). "
        "Considera una alternativa più affidabile."
      )
    if not c.get("registry_match"):
      recs.append(
        f" '{c['local_name']}' non trovato nel Registry MCP. "
        "Potrebbe non essere pubblicato o avere un nome diverso."
      )
  if not recs:
    recs.append(" Tutti i server installati sono ok!")
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


# ============================ MICROFASE 11 ==============================


@server.tool(
  name="pi_capabilities",
  description="Mostra le capacita built-in di pi/Craft Agents. "
  "Utile per capire quali MCP server sono RIDONDANTI (gia presenti in pi) "
  "e quali invece aggiungono valore come integrazioni esterne.",
)
async def pi_caps() -> str:
  """Return markdown summary of pi built-in capabilities."""
  return get_redundancy_help()


# ============================ MAIN ===========================================


def main() -> None:
  """Entry point for mcp-manager."""
  server.run()


if __name__ == "__main__":
  main()

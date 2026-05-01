# Architecture

## Overview

MCP Manager is an MCP (Model Context Protocol) server built with Python and FastMCP. It acts as a **governance and discovery layer** for the MCP ecosystem, connecting to the official MCP Registry and GitHub API.

```
┌─────────────────────────────────────────────────────────┐
│                      LLM / Agent                         │
│  (calls MCP tools via pi/Craft Agents)                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   mcp-manager (FastMCP)                   │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │  Local       │  │  Registry    │  │  Evaluation     │   │
│  │  (config.py) │  │  (registry)  │  │  (capabilities) │   │
│  │              │  │              │  │                 │   │
│  │  .mcp.json   │  │  registry.   │  │  redundancy     │   │
│  │  reader/     │  │  modelconte  │  │  + value score  │   │
│  │  writer      │  │  xtprotocol  │  │  + trust score  │   │
│  └──────┬───────┘  │  .io API     │  └────────┬────────┘   │
│         │          └──────┬───────┘           │            │
│         │                 │                   │            │
└─────────┼─────────────────┼───────────────────┼────────────┘
          │                 │                   │
          ▼                 ▼                   ▼
   ┌──────────┐    ┌──────────────┐    ┌──────────────┐
   │ .mcp.json │    │ MCP Registry  │    │ GitHub API    │
   │ (locale)  │    │ (ufficiale)   │    │ api.github.   │
   │           │    │               │    │ com           │
   └──────────┘    └──────────────┘    └──────────────┘
```

## Core Modules

### `server.py` — Entry point

The FastMCP server that registers all 10 tools. Each tool is a Python async function decorated with `@server.tool()`.

**Tools:**
1. `list_local_servers` — reads `.mcp.json`
2. `search_registry` — queries registry API
3. `get_server_details` — fetches server metadata
4. `assess_trustworthiness` — GitHub trust score
5. `search_with_trust` — combined search + scoring
6. `search_useful_mcp` — smart search (filters redundant)
7. `generate_mcp_config` — config block generator
8. `compare_alternatives` — side-by-side comparison
9. `audit_workspace_mcp` — full workspace audit
10. `registry_health` — registry health check

### `utils/config.py` — Local config

Reads and writes `.mcp.json` files. Supports:
- Automatic discovery (search upward from CWD)
- `MCP_CONFIG_PATH` env var override
- Dry-run mode for safe config generation
- JSON validation with descriptive errors

### `utils/registry.py` — Registry API client

Communicates with `registry.modelcontextprotocol.io/v0.1`:
- `GET /v0.1/servers` — paginated listing with search
- `GET /v0.1/servers/{name}/versions/latest` — server details
- `GET /v0.1/health` + `GET /v0.1/version` — health check

Handles cursor-based pagination, URL encoding, and error states (404, 429, timeout).

### `utils/github.py` — GitHub API client

Evaluates repository trustworthiness via `api.github.com/repos/{owner}/{repo}`:
- In-memory cache with 5-minute TTL
- Rate-limit aware (60 req/h without token, 5,000 with `GITHUB_TOKEN`)

**Trust Score Formula:**
```
stars_score   = min(stars / min_stars, 1.0) × 70
recency_score = updated < 90d ? 20 : max(0, 20 × (1 - (days-90)/270))
forks_score   = min(forks / 10, 1.0) × 10
trust_score   = stars_score + recency_score + forks_score
is_trusted    = trust_score >= 50
```

### `utils/capabilities.py` — pi Awareness Engine

The core innovation: understands what pi/Craft Agents already provides so MCP servers that duplicate built-in functionality are flagged as redundant.

**Redundancy Detection:**
1. Name pattern match (+40 per match)
2. Keyword match in name + description (+15 per match)
3. Known redundant example check (+100)
4. API wrapper penalty (−20)
5. Cloud/infra override (−40 if cloud context detected)

**Value Classification:**
Matches server name/description against 11 value categories (database, cloud, monitoring, etc.) with confidence levels (high/medium/low).

**Composite Score:**
```
composite = trust × 0.40 + (100 - redundancy) × 0.30 + value × 0.30
```

### `data/capabilities.json` — Static capability map

A JSON file that defines 12 built-in capability categories of pi, each with:
- `label` — human-readable name
- `builtin_tools` — list of pi tools in that category
- `replaces_mcp_keywords` — keywords that suggest redundancy
- `replaces_mcp_name_patterns` — name patterns that suggest redundancy
- `redundant_examples` — known examples of redundant MCP servers

## Data Flow

```
1. User calls search_useful_mcp("database", limit=10)
2. server.py → utils/registry.list_servers(search="database", limit=10)
3. Registry API returns [{name, description, repository_url, ...}, ...]
4. For each result:
   a. utils/github.fetch_repo_info(repo_url) → {stars, forks, days_since}
   b. utils/github.compute_trust_score(repo_info) → trust_score (0-100)
   c. utils/capabilities.compute_redundancy(name, desc) → redundancy_score
   d. utils/capabilities.classify_value(name, desc) → value_score, value_label
   e. utils/capabilities.compute_composite_score(...) → composite_score
5. Sort by composite_score descending
6. Filter out redundant servers (if include_redundant=False)
7. Return enriched results to user
```

## Security Boundaries

| Concern | Mitigation |
|---------|------------|
| Network | Only connects to `registry.modelcontextprotocol.io` and `api.github.com` |
| File system | Reads `.mcp.json`; writes only with `dry_run=False` |
| Credentials | `GITHUB_TOKEN` from env var, never logged or stored |
| Execution | No subprocess, no shell — all operations via HTTP |
| Rate limits | In-memory caching (5min TTL) to minimize GitHub API calls |

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `mcp[cli]` | ≥1.27.0 | MCP protocol + FastMCP server |
| `httpx` | ≥0.28.1 | HTTP client for Registry + GitHub APIs |

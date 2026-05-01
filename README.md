# MCP Manager

> **Discover, evaluate, and manage MCP servers from the official registry — with built-in awareness of what pi/Craft Agents already provides.**

MCP Manager is an MCP server that acts as a **governance and discovery hub** for your entire MCP ecosystem. It finds new MCP servers, evaluates trustworthiness, checks if they add real value beyond pi's built-in capabilities, and generates ready-to-use configuration.

**v0.3.0** — [11 tools](.), [62 unit tests](. ), [10 value categories](. ) | [matrixNeo76/mcp-manager](https://github.com/matrixNeo76/mcp-manager)

---

## Features

| Feature | Description |
|---------|-------------|
| Search | Search the official MCP Registry (`registry.modelcontextprotocol.io`) |
| Trust Evaluation | GitHub stars, recency, forks -> trust score (0-100) |
| pi Awareness | Knows what pi/Craft Agents already does — filters out redundant servers |
| Value Classification | Database, Cloud/DevOps, Project Mgmt, Monitoring, Payments, Design, AI/ML, Analytics |
| Composite Scoring | trust_score x 40% + non-redundancy x 30% + value x 30% |
| Workspace Audit | Full audit of your local `.mcp.json` with redundancy warnings |
| Config Generator | Generate ready-to-use `.mcp.json` entries from registry metadata |
| pi Capabilities | See what pi can already do before installing a new MCP server |

---

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
git clone https://github.com/matrixNeo76/mcp-manager.git
cd mcp-manager
uv sync
uv pip install -e .
```

### Run

```bash
# Direct
python -m mcp_manager.server

# Or via the CLI entry point
mcp-manager
```

### Add to your project's `.mcp.json`

```json
{
  "mcpServers": {
    "mcp-manager": {
      "command": "python",
      "args": ["-m", "mcp_manager.server"],
      "cwd": "/path/to/mcp-manager"
    }
  }
}
```

> **Tip:** Set `GITHUB_TOKEN` in your environment for 5,000 API requests/hour instead of 60.

---

## Tools (11)

| Tool | Description |
|------|-------------|
| `list_local_servers` | List MCP servers in your local `.mcp.json` |
| `search_registry(query, limit)` | Search the official MCP Registry |
| `get_server_details(name)` | Detailed info: packages, repository, transports |
| `assess_trustworthiness(url, min_stars)` | GitHub trust score (stars, recency, forks) |
| `search_with_trust(query, limit)` | Search + trust + redundancy + value scoring |
| **`search_useful_mcp(query, limit)`** | Smart search — **filters redundant servers** automatically |
| `compare_alternatives(query)` | Compare servers side-by-side with composite score |
| `generate_mcp_config(name)` | Generate `.mcp.json` block (dry-run by default) |
| `audit_workspace_mcp()` | Full audit with redundancy detection and recommendations |
| `registry_health()` | Check if the MCP Registry is reachable |
| `pi_capabilities()` | Show pi built-in capabilities to understand what is redundant |

---

## Smart Scoring

Every result from `search_useful_mcp` or `search_with_trust` includes:

```
composite_score = trust_score x 0.40    # GitHub stars, recency, forks
                + (100 - redundancy) x 0.30  # pi already has this?
                + value_score x 0.30     # Database? Cloud? API integration?
```

### Trust Score (0-100)

| Component | Weight | Details |
|-----------|--------|---------|
| Stars | 70% | `min(stars / min_stars, 1.0) x 70` |
| Recency | 20% | Updated < 90 days = 20, decays linearly after |
| Forks | 10% | `min(forks / 10, 1.0) x 10` |

### Value Categories

| Category | Score | Examples |
|----------|-------|----------|
| [DB] Database | 90 | PostgreSQL, MySQL, Redis, SQLite |
| [Cloud] Cloud/DevOps | 85 | Kubernetes, Docker, Cloudflare, AWS |
| [$] Payments | 85 | Stripe, PayPal |
| [AI] AI/ML | 85 | Inference, embeddings, model serving |
| [PM] Project Mgmt | 80 | Jira, Linear, Notion, Asana |
| [Chat] Communication | 80 | Slack, Discord, Gmail |
| [Mon] Monitoring | 80 | Sentry, Datadog, Grafana |
| [Design] Design | 75 | Figma, Canva |
| [BI] Analytics/BI | 75 | Dashboards, KPIs, reporting |
| [Media] Media | 75 | YouTube, Spotify, images |
| [Geo] Geolocation | 70 | Maps, coordinates |
| [Shop] E-commerce/CMS | 70 | Shopify, WordPress, Airtable |
| [RED] Redundant | 5-30 | Filesystem, Browser, Search (pi has these) |

---

## Usage Examples

### Find useful MCP servers (not redundant)
```
search_useful_mcp(query="database", limit=10, filter_untrusted=True)
```

### Search with full evaluation
```
search_with_trust(query="notion", limit=10)
```

### Compare alternatives
```
compare_alternatives(query="search", limit=5)
```

### Generate configuration
```
generate_mcp_config(
  server_name="io.github.user/awesome-server",
  server_label="awesome",
  dry_run=True  # False to actually write to .mcp.json
)
```

### Audit workspace with redundancy detection
```
audit_workspace_mcp()
```

### Check pi built-in capabilities
```
pi_capabilities()
```

---

## Testing

```bash
# Unit tests (62 tests, no network required)
uv run python -m pytest tests/ -v

# Smoke test (end-to-end, requires network)
uv run python scripts/smoke_test.py
```

### Test coverage

| Suite | Tests | What it covers |
|-------|-------|----------------|
| `test_capabilities.py` | 25 | Redundancy detection, value classification, composite score |
| `test_github.py` | 18 | URL parsing, trust score formula, rate limit status |
| `test_config.py` | 13 | `.mcp.json` read/write, error handling |
| `test_server.py` | 6 | Tool registration, parameters, behavior |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | — | GitHub API token (5,000 req/h instead of 60) |
| `GITHUB_TIMEOUT` | 15 | GitHub API timeout in seconds |
| `GITHUB_CACHE_TTL` | 300 | GitHub API cache TTL in seconds (default: 5 min) |
| `REGISTRY_TIMEOUT` | 30 | MCP Registry API timeout in seconds |
| `REGISTRY_API_VERSION` | v0.1 | Registry API version (future-proof) |
| `MCP_CONFIG_PATH` | — | Override `.mcp.json` location |

---

## Architecture

```
mcp-manager/
|-- src/mcp_manager/
|   |-- __init__.py         # Package version (0.3.0)
|   |-- server.py           # FastMCP server with 11 tools
|   |-- py.typed            # PEP 561 marker
|   |-- data/
|   |   +-- capabilities.json  # pi built-in capability map
|   +-- utils/
|       |-- config.py       # .mcp.json reader/writer
|       |-- github.py       # GitHub API + trust scoring
|       |-- registry.py     # MCP Registry API client
|       +-- capabilities.py # Redundancy + value scoring engine
|-- tests/
|   |-- test_capabilities.py  # 25 tests
|   |-- test_github.py        # 18 tests
|   |-- test_config.py        # 13 tests
|   +-- test_server.py        # 6 tests
|-- scripts/
|   +-- smoke_test.py       # End-to-end verification
|-- SKILL.md                # Usage documentation
+-- pyproject.toml          # Project config
```

---

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for version history.

---

## Security

- **Read-first**: all tools are read-only by default
- **Write requires explicit flag**: `generate_mcp_config(dry_run=False)`
- **No subprocess execution**: all HTTP via `httpx`
- **No credential exposure**: GitHub token read from env var `GITHUB_TOKEN`
- **Configurable timeouts**: `GITHUB_TIMEOUT`, `REGISTRY_TIMEOUT`
- **Zero emoji**: full cp1252 / ASCII terminal compatibility

---

## License

MIT — see [LICENSE](./LICENSE).

---

## Repository

**[matrixNeo76/mcp-manager](https://github.com/matrixNeo76/mcp-manager)** on GitHub.

# Changelog

All notable changes to MCP Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-05-01

### Added
- `search_useful_mcp` — smart search that filters redundant servers automatically
- `capabilities.py` — redundancy detection and value classification engine
- `capabilities.json` — static map of 12 pi built-in capability categories
- Composite score: trust×40% + non-redundancy×30% + value×30%
- Value categories: Database (90), Cloud/DevOps (85), Payments (85), Project Mgmt (80), etc.
- Redundant server detection in `audit_workspace_mcp`

### Updated
- `search_with_trust` — now includes redundancy, value, and composite scores
- `compare_alternatives` — shows redundancy status for each alternative
- `audit_workspace_mcp` — detects redundant servers and recommends removal

### Documentation
- Added `ARCHITECTURE.md`, `AGENTS.md`, `CLAUDE.md`, `CHANGELOG.md`, `CONTRIBUTING.md`
- Comprehensive README with features, scoring, and usage

## [0.1.0] — 2026-05-01

### Added
- Initial MCP Manager server with 9 tools
- `list_local_servers` — inspect local `.mcp.json`
- `search_registry` — search the official MCP Registry
- `get_server_details` — detailed server metadata
- `assess_trustworthiness` — GitHub trust score (0–100)
- `search_with_trust` — combined search + trust ranking
- `generate_mcp_config` — dry-run config generation
- `compare_alternatives` — side-by-side server comparison
- `audit_workspace_mcp` — workspace audit with recommendations
- `registry_health` — registry health check
- GitHub repository: `matrixNeo76/mcp-manager`

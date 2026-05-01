# Changelog

All notable changes to MCP Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] — 2026-05-02

### Added
- CLI flags: `--version`, `--http`, `--port`, `--host` via argparse
- GitHub Actions CI: Python 3.12 + 3.13 matrix
- `GITHUB_CACHE_TTL` env var for configurable cache
- `X-RateLimit-Reset` tracking (resets_in_minutes in rate limit warnings)
- `__main__.py` for `python -m mcp_manager` support
- `.gitattributes` for consistent LF line endings

### Fixed
- W1: `prefer_remote` parameter added to `generate_mcp_config` signature
- W2: `--help` now shows `mcp-manager` instead of `__main__.py`
- W3: `--http` mode documented as experimental (proper SSE transport support planned)

### Changed
- Version bumped to 0.4.0
- `write_mcp_config_entry` now uses `ensure_ascii=True` for safe JSON
- Rate limit warnings include reset time ("Resetta tra ~Xmin")
- Line endings normalized via `.gitattributes` (LF)

### Documentation
- README: added `GITHUB_CACHE_TTL` to env vars table

## [0.3.0] — 2026-05-02

### Added
- `pi_capabilities` tool — shows pi/Craft Agents built-in capabilities (11th tool)
- `tests/` — 62 unit tests across 4 test files (test_capabilities, test_github, test_config, test_server)
- `scripts/smoke_test.py` — end-to-end smoke test (7 checks)
- `src/mcp_manager/py.typed` — PEP 561 marker for typing strict mode
- `src/mcp_manager/__init__.py` — centralized `__version__`
- `GITHUB_TIMEOUT` env var — configurable GitHub API timeout
- `REGISTRY_API_VERSION` env var — future-proof API version
- `prefer_remote` parameter on `generate_mcp_config` — allows choosing remote over package
- `also_available_as_remote` flag in config generation response
- Multi-label support: `value_types[]` on classify_value
- Value categories: Analytics/BI, AI/ML

### Fixed
- Emoji removed from all labels (23 occurrences across 3 files) — fixes cp1252 crash on Windows
- `MCP_CONFIG_PATH` now raises error when pointing to non-existent file
- Dead code eliminated: `get_redundancy_help` now exposed as `pi_capabilities` tool
- `composite_score(0,0,0)` now returns 0 instead of 30
- Special characters in server names now get validation error instead of 404
- Registry search in audit increased from 3 to 10 for better matching
- GitHub rate limit warnings added to enriched results
- `search_useful_mcp` correctly filters by `filter_untrusted` before returning

### Changed
- Version bumped to 0.3.0
- Trust evaluation now runs in parallel (`asyncio.gather`, max 5 concurrent)
- Hardcoded timeouts replaced with env vars (`GITHUB_TIMEOUT`, `REGISTRY_TIMEOUT`)
- `.gitignore` covers egg-info, build, dist, IDE files

### Documentation
- README updated with 11 tools, 62 tests, env vars table, architecture
- SKILL.md updated with all tools, composite scoring, filters

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

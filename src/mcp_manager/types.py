"""Type definitions for MCP Manager.

Structured return types for all tools and utilities.
Using TypedDict for runtime-accessible dict types.
"""

from typing import TypedDict


class ServerEntry(TypedDict):
    """A server from the MCP Registry listing."""
    name: str
    title: str | None
    description: str
    version: str
    repository_url: str | None
    repository_source: str | None
    repository_id: str | None
    website_url: str | None
    status: str
    is_latest: bool
    published_at: str | None
    updated_at: str | None


class LocalServer(TypedDict):
    """A server configured in local .mcp.json."""
    name: str
    command: str
    args: list[str]
    cwd: str | None
    env: dict[str, str]


class RepoInfo(TypedDict):
    """Information from GitHub API."""
    found: bool
    stars: int
    forks: int
    open_issues: int
    description: str
    last_push: str
    days_since_update: int
    language: str | None
    topics: list[str]
    error: str | None


class TrustScore(TypedDict):
    """Computed trust score (0-100)."""
    trust_score: float
    is_trusted: bool
    stars_score: float
    recency_score: float
    forks_score: float
    min_stars_required: int
    warnings: list[str]


class RedundancyResult(TypedDict):
    """Result of redundancy check against pi built-in capabilities."""
    redundancy_score: int
    redundant: bool
    redundant_category: str | None
    redundant_reason: str | None


class ValueResult(TypedDict):
    """Result of value classification (what pi CAN'T do)."""
    value_type: str
    value_score: int
    value_label: str
    value_match_confidence: str
    value_types: list[str]


class EnrichedServer(TypedDict):
    """A server enriched with trust, redundancy, value, and composite scores."""
    name: str
    title: str | None
    description: str
    version: str
    repository_url: str | None
    status: str
    stars: int
    forks: int
    trust_score: float
    is_trusted: bool
    redundancy_score: int
    redundant: bool
    redundant_category: str | None
    redundant_reason: str | None
    value_type: str
    value_score: int
    value_label: str
    value_match_confidence: str
    composite_score: float


class ServerDetail(TypedDict):
    """Detailed server information from the registry."""
    found: bool
    name: str | None
    title: str | None
    description: str | None
    version: str | None
    website_url: str | None
    status: str | None
    is_latest: bool | None
    published_at: str | None
    updated_at: str | None
    repository: dict | None
    packages: list[dict] | None
    remotes: list[dict] | None
    icons: list[dict] | None
    error: str | None


class AuditEntry(TypedDict):
    """Single server entry in an audit report."""
    local_name: str
    command: str
    registry_match: str | None
    registry_version: str | None
    is_outdated: bool | None
    trust_score: float | None
    is_trusted: bool | None
    redundant: bool
    redundant_reason: str | None
    value_label: str
    composite_score: float | None
    warnings: list[str]


class RateLimitStatus(TypedDict):
    """GitHub API rate limit status."""
    remaining: int | None
    limit: int | None
    resets_in_seconds: int | None
    resets_in_minutes: float | None
    has_token: bool
    is_low: bool


class RegistryHealth(TypedDict):
    """MCP Registry health check result."""
    reachable: bool
    servers_count: int
    response_time_ms: int
    api_version: str
    error: str | None

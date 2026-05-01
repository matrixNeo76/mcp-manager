"""GitHub API client for evaluating repository trustworthiness."""

import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx

GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Simple in-memory cache: repo_url -> (timestamp, data)
_cache: dict[str, tuple[float, dict[str, Any]]] = {}
CACHE_TTL = int(os.environ.get("GITHUB_CACHE_TTL", "300"))  # seconds, default 5 min

# Configurable timeout (env override)
GITHUB_TIMEOUT = int(os.environ.get("GITHUB_TIMEOUT", "15"))

# GitHub rate limit tracking (updated from response headers)
_rate_limit_remaining: int | None = None
_rate_limit_limit: int | None = None
_rate_limit_reset: int | None = None  # Unix timestamp when limit resets


def get_rate_limit_status() -> dict:
    """Return current GitHub API rate limit status."""
    resets_in = None
    if _rate_limit_reset is not None:
        resets_in = max(0, _rate_limit_reset - int(time.time()))
    return {
        "remaining": _rate_limit_remaining,
        "limit": _rate_limit_limit,
        "resets_in_seconds": resets_in,
        "resets_in_minutes": round(resets_in / 60, 1) if resets_in is not None else None,
        "has_token": bool(GITHUB_TOKEN),
        "is_low": _rate_limit_remaining is not None and _rate_limit_remaining < 10,
    }


def _parse_github_repo(repository_url: str) -> tuple[str, str] | None:
    """Extract owner/repo from a GitHub URL. Returns None if not a GitHub URL."""
    url = repository_url.rstrip("/")
    if "github.com/" not in url:
        return None

    parts = url.split("github.com/")[-1].split("/")
    if len(parts) >= 2:
        return parts[0], parts[1].replace(".git", "")
    return None


def _build_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "mcp-manager/0.1.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def fetch_repo_info(repository_url: str, force_refresh: bool = False) -> dict[str, Any]:
    """Fetch repository information from GitHub API.

    Args:
        repository_url: Full GitHub repository URL
        force_refresh: If True, bypass in-memory cache

    Returns a dict with:
      - found: bool
      - stars: int
      - forks: int
      - open_issues: int
      - description: str
      - last_push: str (ISO date)
      - days_since_update: int
      - language: str | None
      - topics: list[str]
      - error: str | None
    """
    # Check cache
    now = time.time()
    cached = _cache.get(repository_url)
    if cached and (now - cached[0]) < CACHE_TTL and not force_refresh:
        return cached[1]

    owner_repo = _parse_github_repo(repository_url)
    if not owner_repo:
        result = {
            "found": False,
            "stars": 0,
            "forks": 0,
            "open_issues": 0,
            "description": "",
            "last_push": "",
            "days_since_update": 9999,
            "language": None,
            "topics": [],
            "error": "Not a GitHub repository URL",
        }
        _cache[repository_url] = (now, result)
        return result

    owner, repo = owner_repo
    url = f"{GITHUB_API}/repos/{owner}/{repo}"

    try:
        with httpx.Client(timeout=GITHUB_TIMEOUT) as client:
            resp = client.get(url, headers=_build_headers())

        if resp.status_code == 404:
            result = {
                "found": False,
                "stars": 0,
                "forks": 0,
                "open_issues": 0,
                "description": "",
                "last_push": "",
                "days_since_update": 9999,
                "language": None,
                "topics": [],
                "error": f"Repository {owner}/{repo} not found (404)",
            }
        elif resp.status_code == 403:
            result = {
                "found": False,
                "stars": 0,
                "forks": 0,
                "open_issues": 0,
                "description": "",
                "last_push": "",
                "days_since_update": 9999,
                "language": None,
                "topics": [],
                "error": f"GitHub API rate limit exceeded. Set GITHUB_TOKEN for 5,000 req/h instead of 60.",
            }
        elif resp.status_code != 200:
            result = {
                "found": False,
                "stars": 0,
                "forks": 0,
                "open_issues": 0,
                "description": "",
                "last_push": "",
                "days_since_update": 9999,
                "language": None,
                "topics": [],
                "error": f"GitHub API returned {resp.status_code}",
            }
        else:
            data = resp.json()
            last_push_str = data.get("pushed_at", "")
            days_since = 9999
            if last_push_str:
                try:
                    pushed = datetime.fromisoformat(
                        last_push_str.replace("Z", "+00:00")
                    )
                    days_since = (datetime.now(timezone.utc) - pushed).days
                except ValueError:
                    pass

            result = {
                "found": True,
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "description": data.get("description") or "",
                "last_push": last_push_str,
                "days_since_update": days_since,
                "language": data.get("language"),
                "topics": data.get("topics", []),
                "error": None,
            }
    except httpx.TimeoutException:
        result = {
            "found": False, "stars": 0, "forks": 0, "open_issues": 0,
            "description": "", "last_push": "", "days_since_update": 9999,
            "language": None, "topics": [],
            "error": "Timeout contacting GitHub API",
        }
    except Exception as e:
        result = {
            "found": False, "stars": 0, "forks": 0, "open_issues": 0,
            "description": "", "last_push": "", "days_since_update": 9999,
            "language": None, "topics": [],
            "error": str(e),
        }

    # Track rate limit from response headers (if available)
    try:
        remaining = resp.headers.get("X-RateLimit-Remaining")
        limit = resp.headers.get("X-RateLimit-Limit")
        reset = resp.headers.get("X-RateLimit-Reset")
        if remaining is not None:
            _rate_limit_remaining = int(remaining)
        if limit is not None:
            _rate_limit_limit = int(limit)
        if reset is not None:
            _rate_limit_reset = int(reset)
    except (NameError, AttributeError):
        pass  # resp not defined (e.g., timeout or parse error)

    _cache[repository_url] = (time.time(), result)
    return result


def compute_trust_score(repo_info: dict[str, Any], min_stars: int = 10) -> dict[str, Any]:
    """Compute a trust score (0-100) from repository info.

    Formula:
      - stars_score = min(stars / min_stars, 1.0) * 70
      - recency_score = updated < 90 days ? 20 : max(0, 20 * (1 - (days-90)/270))
      - forks_score = min(forks / 10, 1.0) * 10
      - trust_score = stars_score + recency_score + forks_score
      - is_trusted = trust_score >= 50
    """
    if not repo_info.get("found"):
        return {
            "trust_score": 0,
            "is_trusted": False,
            "stars_score": 0,
            "recency_score": 0,
            "forks_score": 0,
            "min_stars_required": min_stars,
            "warnings": [repo_info.get("error", "Repository not found")],
        }

    stars = repo_info["stars"]
    forks = repo_info["forks"]
    days_since = repo_info["days_since_update"]

    stars_score = min(stars / max(min_stars, 1), 1.0) * 70

    if days_since <= 90:
        recency_score = 20
    elif days_since <= 360:
        recency_score = max(0, 20 * (1 - (days_since - 90) / 270))
    else:
        recency_score = 0

    forks_score = min(forks / 10, 1.0) * 10

    trust_score = round(stars_score + recency_score + forks_score, 1)
    is_trusted = trust_score >= 50

    warnings = []
    if stars < min_stars:
        warnings.append(
            f"Only {stars} stars (minimum recommended: {min_stars})"
        )
    if days_since > 180:
        warnings.append(
            f"Not updated in {days_since} days (> 6 months)"
        )

    return {
        "trust_score": trust_score,
        "is_trusted": is_trusted,
        "stars_score": round(stars_score, 1),
        "recency_score": round(recency_score, 1),
        "forks_score": round(forks_score, 1),
        "min_stars_required": min_stars,
        "warnings": warnings,
    }

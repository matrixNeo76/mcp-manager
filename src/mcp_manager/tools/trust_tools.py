"""Tool: assess_trustworthiness — evaluate GitHub repo trust score."""

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp_manager.utils.github import fetch_repo_info, compute_trust_score


def register(server: FastMCP) -> None:
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

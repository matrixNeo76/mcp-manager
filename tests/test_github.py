"""Unit test per GitHub URL parsing e trust score."""

from mcp_manager.utils.github import (
    compute_trust_score,
    _parse_github_repo,
    get_rate_limit_status,
)


class TestParseGithubRepo:
    """Verifica parsing URL GitHub."""

    def test_standard_url(self):
        assert _parse_github_repo("https://github.com/owner/repo") == ("owner", "repo")

    def test_git_suffix(self):
        assert _parse_github_repo("https://github.com/owner/repo.git") == ("owner", "repo")

    def test_trailing_slash(self):
        assert _parse_github_repo("https://github.com/owner/repo/") == ("owner", "repo")

    def test_subfolder(self):
        assert _parse_github_repo("https://github.com/owner/repo/subfolder") == ("owner", "repo")

    def test_http(self):
        assert _parse_github_repo("http://github.com/owner/repo") == ("owner", "repo")

    def test_non_github(self):
        assert _parse_github_repo("https://gitlab.com/owner/repo") is None

    def test_empty(self):
        assert _parse_github_repo("") is None

    def test_invalid(self):
        assert _parse_github_repo("not a url") is None


class TestTrustScore:
    """Verifica formula del trust score."""

    def test_high_trust(self):
        s = compute_trust_score({
            "found": True, "stars": 10000, "forks": 500,
            "days_since_update": 5,
        })
        assert s["is_trusted"] is True
        assert s["trust_score"] == 100.0

    def test_zero_stats(self):
        s = compute_trust_score({
            "found": True, "stars": 0, "forks": 0,
            "days_since_update": 999,
        })
        assert s["trust_score"] == 0.0
        assert s["is_trusted"] is False

    def test_not_found(self):
        s = compute_trust_score({"found": False})
        assert s["trust_score"] == 0
        assert s["is_trusted"] is False
        assert len(s["warnings"]) == 1

    def test_min_stars_effect(self):
        s50 = compute_trust_score({"found": True, "stars": 50, "forks": 5, "days_since_update": 30}, min_stars=100)
        assert s50["trust_score"] < 100  # Non raggiunge il max

        s100 = compute_trust_score({"found": True, "stars": 100, "forks": 10, "days_since_update": 30}, min_stars=100)
        assert s100["trust_score"] == 100.0

    def test_recency_decay(self):
        # Oltre 90 giorni, recency score inizia a decadere
        recent = compute_trust_score({"found": True, "stars": 100, "forks": 10, "days_since_update": 30})
        old = compute_trust_score({"found": True, "stars": 100, "forks": 10, "days_since_update": 200})
        assert recent["recency_score"] == 20  # max recency
        assert old["recency_score"] < 20  # decayed

    def test_warnings_for_low_stars(self):
        s = compute_trust_score({"found": True, "stars": 3, "forks": 1, "days_since_update": 5}, min_stars=10)
        assert len(s["warnings"]) >= 1

    def test_warnings_for_old_repo(self):
        s = compute_trust_score({"found": True, "stars": 500, "forks": 50, "days_since_update": 400})
        assert len(s["warnings"]) >= 1


class TestRateLimitStatus:
    """Verifica stato rate limit."""

    def test_returns_dict(self):
        status = get_rate_limit_status()
        assert "remaining" in status
        assert "limit" in status
        assert "has_token" in status
        assert "is_low" in status

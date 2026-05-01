"""Test per Registry API client."""

from mcp_manager.utils.registry import (
    list_servers,
    get_server_detail,
    registry_health,
)


class TestListServers:
    """Verifica elenco server dal registry."""

    def test_no_results(self):
        results = list_servers(search="xyznonexistent12345", limit=5)
        assert len(results) == 0

    def test_returns_list(self):
        results = list_servers(search="postgres", limit=2)
        assert isinstance(results, list)

    def test_results_have_required_keys(self):
        results = list_servers(search="postgres", limit=1)
        if results:
            entry = results[0]
            assert "name" in entry
            assert "description" in entry
            assert "version" in entry


class TestGetServerDetail:
    """Verifica dettagli server."""

    def test_invalid_name_returns_error(self):
        result = get_server_detail("invalid@name!")
        assert result.get("found") is False
        assert "Invalid" in result.get("error", "")

    def test_nonexistent_returns_not_found(self):
        result = get_server_detail("nonexistent.test/server")
        assert result.get("found") is False


class TestRegistryHealth:
    """Verifica health check."""

    def test_returns_dict_with_keys(self):
        health = registry_health()
        assert "reachable" in health
        assert "servers_count" in health
        assert "response_time_ms" in health
        assert isinstance(health.get("reachable"), bool)

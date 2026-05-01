"""Unit test per registrazione tool del server MCP."""

import asyncio
from mcp_manager.server import server


class TestToolRegistration:
    """Verifica che tutti i tool siano registrati."""

    def _get_tools(self):
        return asyncio.run(server.list_tools())

    def test_tools_count(self):
        tools = self._get_tools()
        assert len(tools) == 11, f"Expected 11 tools, got {len(tools)}"

    def test_required_tools_exist(self):
        tools = self._get_tools()
        names = [t.name for t in tools]
        required = [
            "list_local_servers",
            "search_registry",
            "get_server_details",
            "assess_trustworthiness",
            "search_with_trust",
            "search_useful_mcp",
            "generate_mcp_config",
            "compare_alternatives",
            "audit_workspace_mcp",
            "registry_health",
            "pi_capabilities",
        ]
        for name in required:
            assert name in names, f"Tool '{name}' not registered"

    def test_no_tool_without_description(self):
        tools = self._get_tools()
        for t in tools:
            assert t.description, f"Tool '{t.name}' has no description"

    def test_tool_parameters_have_types(self):
        tools = self._get_tools()
        for t in tools:
            props = t.inputSchema.get("properties", {})
            for pname, pschema in props.items():
                assert "type" in pschema or "anyOf" in pschema or "oneOf" in pschema, \
                    f"Tool '{t.name}' param '{pname}' has no type"

    def test_search_useful_has_correct_defaults(self):
        tools = self._get_tools()
        useful = next(t for t in tools if t.name == "search_useful_mcp")
        props = useful.inputSchema.get("properties", {})
        assert props.get("filter_untrusted", {}).get("default") is True
        assert props.get("include_redundant", {}).get("default") is False


class TestToolBehavior:
    """Verifica comportamento dei tool (senza rete)."""

    def test_pi_capabilities_returns_string(self):
        text, data = asyncio.run(server.call_tool("pi_capabilities", {}))
        result = text[0].text if text else ""
        assert len(result) > 100
        assert "Filesystem" in result
        assert "read" in result

    def test_registry_health_returns_dict(self):
        text, data = asyncio.run(server.call_tool("registry_health", {}))
        assert "reachable" in data
        assert "servers_count" in data

    def test_list_local_servers_returns_list(self):
        text, data = asyncio.run(server.call_tool("list_local_servers", {}))
        assert isinstance(data.get("result", data), list)

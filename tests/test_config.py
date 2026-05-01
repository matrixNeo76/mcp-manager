"""Unit test per lettura/scrittura .mcp.json."""

import json
import os
import tempfile
import warnings
from pathlib import Path

from mcp_manager.utils.config import (
    find_mcp_config,
    list_local_servers,
    read_mcp_config,
    write_mcp_config_entry,
)

# Suppress Windows tempfile cleanup warnings
warnings.filterwarnings("ignore", message=".*TemporaryDirectory.*")


def _write_cfg(tmp: str, data: dict) -> Path:
    """Helper: write .mcp.json in tmp dir and return path."""
    cfg = Path(tmp) / ".mcp.json"
    cfg.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return cfg


class TestFindConfig:
    """Verifica ricerca file .mcp.json."""

    def test_no_config_raises_error(self):
        try:
            find_mcp_config("/nonexistent/path_xyzzy_12345")
            assert False, "Doveva sollevare FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_mcp_config_path_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _write_cfg(tmp, {})
            os.environ["MCP_CONFIG_PATH"] = str(cfg)
            try:
                path = find_mcp_config()
                assert path.exists()
            finally:
                del os.environ["MCP_CONFIG_PATH"]

    def test_mcp_config_path_bogus_raises(self):
        old = os.environ.pop("MCP_CONFIG_PATH", None)
        os.environ["MCP_CONFIG_PATH"] = "/fake/nonexistent/.mcp.json"
        try:
            find_mcp_config()
            assert False, "Doveva sollevare FileNotFoundError"
        except FileNotFoundError as e:
            assert "MCP_CONFIG_PATH" in str(e)
        finally:
            if old:
                os.environ["MCP_CONFIG_PATH"] = old
            else:
                os.environ.pop("MCP_CONFIG_PATH", None)


class TestListLocalServers:
    """Verifica elenco server locali."""

    def test_no_config_returns_empty_list(self):
        assert list_local_servers("/nonexistent/path") == []

    def test_with_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_cfg(tmp, {
                "mcpServers": {
                    "server-a": {"command": "python", "args": ["-m", "a"]},
                    "server-b": {"command": "node", "args": ["b.js"]},
                }
            })
            servers = list_local_servers(str(tmp))
            assert len(servers) == 2
            names = [s["name"] for s in servers]
            assert "server-a" in names
            assert "server-b" in names

    def test_empty_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_cfg(tmp, {})
            assert list_local_servers(str(tmp)) == []

    def test_malformed_json_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".mcp.json").write_text("not json", encoding="utf-8")
            try:
                read_mcp_config(str(tmp))
                assert False, "Doveva sollevare ValueError"
            except ValueError:
                pass

    def test_mcp_servers_not_dict_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_cfg(tmp, {"mcpServers": "string"})
            try:
                read_mcp_config(str(tmp))
                assert False, "Doveva sollevare ValueError"
            except ValueError:
                pass


class TestWriteConfigEntry:
    """Verifica scrittura entry in .mcp.json."""

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_cfg(tmp, {})
            result = write_mcp_config_entry("test-srv", {"command": "x"}, path=tmp, dry_run=True)
            assert result["operation"] == "create"
            # File unchanged
            data = json.loads((Path(tmp) / ".mcp.json").read_text(encoding="utf-8"))
            assert "mcpServers" not in data

    def test_dry_run_false_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_cfg(tmp, {})
            result = write_mcp_config_entry("test-srv", {"command": "x"}, path=tmp, dry_run=False)
            assert result["operation"] == "created"
            data = json.loads((Path(tmp) / ".mcp.json").read_text(encoding="utf-8"))
            assert "test-srv" in data["mcpServers"]

    def test_update_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_cfg(tmp, {"mcpServers": {"old": {"command": "old"}}})
            r = write_mcp_config_entry("old", {"command": "new"}, path=tmp, dry_run=True)
            assert r["operation"] == "update"

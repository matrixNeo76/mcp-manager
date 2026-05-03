# Piano Esecutivo V5 — 15 Gap in 9 Microfasi

Ordine: Architettura → Qualità → Feature (build on solid foundation).

---

## 📦 Sprint 1 — Architettura (4 microfasi, ~115 min)

### MF 1.1 — Registry cache + Thread safety globals (A4 + A3)

**File**: `src/mcp_manager/utils/registry.py`, `src/mcp_manager/utils/github.py`

**Task A4 — Registry cache** (10 min):
1. In `registry.py`, aggiungere dopo `REGISTRY_TIMEOUT`:
```python
import time
from functools import lru_cache

# Cache configurabile
REGISTRY_CACHE_TTL = int(os.environ.get("REGISTRY_CACHE_TTL", "60"))  # 60 secondi
_cache_registry: dict[str, tuple[float, Any]] = {}
```
2. Wrappare `list_servers()` con cache check:
```python
def list_servers(search=None, limit=20, version="latest", updated_since=None):
    cache_key = f"{search}:{limit}:{version}:{updated_since}"
    now = time.time()
    cached = _cache_registry.get(cache_key)
    if cached and (now - cached[0]) < REGISTRY_CACHE_TTL:
        return cached[1]
    # ... existing logic ...
    _cache_registry[cache_key] = (time.time(), result)
    return result
```

**Task A3 — Thread safety** (10 min):
1. In `github.py`, racchiudere le variabili globali in un oggetto:
```python
import threading

class RateLimitTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self._remaining: int | None = None
        self._limit: int | None = None
        self._reset: int | None = None
    
    def update(self, remaining=None, limit=None, reset=None):
        with self._lock:
            if remaining is not None: self._remaining = int(remaining)
            if limit is not None: self._limit = int(limit)
            if reset is not None: self._reset = int(reset)
    
    def status(self) -> dict:
        with self._lock:
            resets_in = max(0, self._reset - int(time.time())) if self._reset else None
            return {
                "remaining": self._remaining, "limit": self._limit,
                "resets_in_seconds": resets_in,
                "resets_in_minutes": round(resets_in / 60, 1) if resets_in else None,
                "has_token": bool(GITHUB_TOKEN),
                "is_low": self._remaining is not None and self._remaining < 10,
            }

rate_limit = RateLimitTracker()
```
2. Sostituire tutti i `_rate_limit_*` con `rate_limit.update(...)` e `rate_limit.status()`
3. Aggiornare `get_rate_limit_status()` → delegare a `rate_limit.status()`

**Verifica**:
```bash
uv run python -m pytest tests/ -v --tb=short
# 70+ test passano
```

---

### MF 1.2 — Tipi strutturati con TypedDict (A2)

**File nuovo**: `src/mcp_manager/types.py`

**Task** (30 min):
1. Creare `types.py` con tutti i tipi:
```python
"""Type definitions for MCP Manager."""
from typing import TypedDict, NotRequired

class ServerEntry(TypedDict):
    """A server from the MCP Registry listing."""
    name: str
    title: str | None
    description: str
    version: str
    repository_url: str | None
    status: str

class TrustScore(TypedDict):
    trust_score: float
    is_trusted: bool
    stars_score: float
    recency_score: float
    forks_score: float
    min_stars_required: int
    warnings: list[str]

class RedundancyResult(TypedDict):
    redundancy_score: int
    redundant: bool
    redundant_category: str | None
    redundant_reason: str | None

class ValueResult(TypedDict):
    value_type: str
    value_score: int
    value_label: str
    value_match_confidence: str
    value_types: list[str]

class EnrichedServer(ServerEntry):
    """A server enriched with trust, redundancy, and value scores."""
    trust_score: float
    is_trusted: bool
    stars: int
    forks: int
    redundancy_score: int
    redundant: bool
    value_score: int
    value_type: str
    value_label: str
    composite_score: float

class LocalServer(TypedDict):
    name: str
    command: str
    args: list[str]
    cwd: str | None
    env: dict[str, str]
```

2. Aggiornare gradualmente i tipi di ritorno in tutti i moduli. Non tutto in una volta — iniziare da `compute_trust_score` e `compute_redundancy`.

**Verifica**:
```bash
uv run basedpyright src/mcp_manager/types.py
# Nessun errore di tipo
```

---

### MF 1.3 — Estrarre tool in moduli separati (A1)

**File**: `src/mcp_manager/tools/` (6 nuovi file)
**File**: `src/mcp_manager/server.py` (ridotto a ~50 linee)

**Task** (60 min):

1. Creare `src/mcp_manager/tools/__init__.py`:
```python
"""Tool modules for MCP Manager."""
```

2. Creare `src/mcp_manager/tools/local_tools.py`:
```python
"""list_local_servers tool."""
from mcp.server.fastmcp import FastMCP

def register(server: FastMCP) -> None:
    @server.tool(name="list_local_servers", description="...")
    async def list_local() -> list[dict]:
        from mcp_manager.utils.config import list_local_servers as _list
        return _list()
```

3. Creare `src/mcp_manager/tools/search_tools.py` — raggruppa:
   - `search_registry`
   - `search_with_trust`
   - `search_useful_mcp`
   - `_enrich_with_scores`
   - `_attach_rate_warning`

4. Creare `src/mcp_manager/tools/trust_tools.py`:
   - `assess_trustworthiness`

5. Creare `src/mcp_manager/tools/config_tools.py`:
   - `generate_mcp_config`

6. Creare `src/mcp_manager/tools/audit_tools.py`:
   - `audit_workspace_mcp`
   - `compare_alternatives`
   - `pi_capabilities`

7. Creare `src/mcp_manager/tools/info_tools.py`:
   - `get_server_details`
   - `registry_health`

8. Ridurre `server.py` a:
```python
"""MCP Manager — MCP server entry point."""
import argparse
from mcp.server.fastmcp import FastMCP
from mcp_manager import __version__

server = FastMCP(name="mcp-manager", instructions="...")

# Register all tool modules
from mcp_manager.tools import (
    local_tools, search_tools, trust_tools,
    config_tools, audit_tools, info_tools,
)
local_tools.register(server)
search_tools.register(server)
trust_tools.register(server)
config_tools.register(server)
audit_tools.register(server)
info_tools.register(server)

def main() -> None:
    parser = argparse.ArgumentParser(prog="mcp-manager", ...)
    # ... (CLI args rimangono qui)
    args = parser.parse_args()
    if args.http:
        print("HTTP mode experimental")
        parser.exit(1)
    else:
        server.run()
```

**Verifica**:
```bash
uv run python -m pytest tests/ -v --tb=short
# 70+ test devono ancora passare
# (alcuni test potrebbero rompersi se importano da server.py)
```

---

### MF 1.4 — Aggiornare test dopo refactoring (A1 fix)

**File**: `tests/test_server.py`

**Task** (15 min):
1. Aggiornare import se `server.py` cambia struttura
2. Aggiungere test per l'entry point `main()`:
```python
class TestMain:
    def test_version_flag(self):
        import subprocess, sys
        r = subprocess.run([sys.executable, '-m', 'mcp_manager', '--version'],
                          capture_output=True, text=True, timeout=5)
        assert r.returncode == 0
        assert 'v0.4.0' in r.stdout
```

**Verifica**:
```bash
uv run python -m mcp_manager --version
uv run python -m pytest tests/ -v
```

---

## 📦 Sprint 2 — Qualita (2 microfasi, ~80 min)

### MF 2.1 — Test CLI + prefer_remote + mock Registry (B1 + B3 + B2)

**File nuovo**: `tests/test_cli.py`
**File nuovo/aggiornato**: `tests/test_server.py`, `tests/test_registry.py`

**Task B1** (15 min):
```python
# tests/test_cli.py
import subprocess, sys

class TestCLI:
    def test_version(self):
        r = subprocess.run([sys.executable, '-m', 'mcp_manager', '--version'],
                          capture_output=True, text=True)
        assert r.returncode == 0
        assert 'v' in r.stdout

    def test_help(self):
        r = subprocess.run([sys.executable, '-m', 'mcp_manager', '--help'],
                          capture_output=True, text=True)
        assert r.returncode == 0
        assert 'mcp-manager' in r.stdout

    def test_nonexistent_server(self):
        r = subprocess.run(
            [sys.executable, '-m', 'mcp_manager', 'generate_mcp_config', 'nonexistent'],
            capture_output=True, text=True)
        # Should fail gracefully
        assert r.returncode != 0 or 'error' in r.stdout.lower()
```

**Task B2** (20 min):
Aggiungere mock per Registry API in `test_registry.py`:
```python
from unittest.mock import patch, MagicMock

class TestListServersMocked:
    @patch('mcp_manager.utils.registry.httpx.Client')
    def test_mocked_response(self, mock_client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "servers": [
                {"server": {"name": "test/srv1", "description": "d", "version": "1"}, "_meta": {}}
            ],
            "metadata": {"count": 1, "nextCursor": None},
        }
        mock_client.return_value.__enter__.return_value.get.return_value = mock_resp
        results = list_servers(search="test", limit=5)
        assert len(results) == 1
```

**Task B3** (10 min):
Aggiungere test per `prefer_remote`:
```python
# Nei test_server.py
def test_gen_config_prefer_remote(self):
    text, data = asyncio.run(server.call_tool('generate_mcp_config', {
        'server_name': 'io.github.containers/kubernetes-mcp-server',
        'prefer_remote': True, 'dry_run': True,
    }))
    entry = data.get('result', data)
    assert 'url' in str(entry) or 'also_available_as_package' in str(entry)
```

**Verifica**:
```bash
uv run python -m pytest tests/ -v --tb=short
# Nuovi 7+ test si aggiungono
```

---

### MF 2.2 — Property-based test + battery ridondanza (B4 + B5)

**File**: `tests/test_capabilities.py`
**File**: `pyproject.toml` (aggiungere hypothesis)

**Task B4** (20 min):
```python
# tests/test_capabilities.py — aggiungere
from hypothesis import given, strategies as st

class TestTrustScoreProperty:
    @given(
        stars=st.integers(min_value=0, max_value=100000),
        forks=st.integers(min_value=0, max_value=50000),
        days=st.integers(min_value=0, max_value=2000),
    )
    def test_trust_score_bounds(self, stars, forks, days):
        s = compute_trust_score({
            "found": True, "stars": stars, "forks": forks,
            "days_since_update": days,
        })
        assert 0 <= s["trust_score"] <= 100
        assert s["is_trusted"] == (s["trust_score"] >= 50)
```

**Task B5** (15 min):
Aggiungere 50+ combinazioni nome/descrizione a `test_capabilities.py`:
```python
REDUNDANCY_TEST_CASES = [
    # (name, description, expected_redundant)
    ("io.github.x/filesystem", "file operations", True),
    ("microsoft/playwright-mcp", "browser automation", True),
    ("com.letta/memory-mcp", "knowledge graph", True),
    ("io.github.containers/kubernetes", "K8s cluster management", False),
    ("ai.waystation/postgres", "PostgreSQL queries", False),
    ("com.figma.mcp/mcp", "Figma design API", False),
    ("io.github.getsentry/sentry-mcp", "error tracking", False),
    # ... 50+ casi
]

class TestBulkRedundancy:
    @pytest.mark.parametrize("name,desc,expected", REDUNDANCY_TEST_CASES)
    def test_redundancy(self, name, desc, expected):
        r = compute_redundancy(name, desc)
        assert r["redundant"] == expected, f"{name}: expected {expected}, got {r['redundant']}"
```

**Verifica**:
```bash
uv pip install hypothesis
uv run python -m pytest tests/ -v --tb=short
# 120+ test totali
```

---

## 📦 Sprint 3 — Feature (3 microfasi, ~140 min)

### MF 3.1 — Filtro value_type + Confronto versioni (C1 + C2)

**File**: `src/mcp_manager/server.py`, `src/mcp_manager/utils/capabilities.py`

**Task C1** (15 min):
1. Aggiungere parametro `value_type: str = ""` a `search_useful_mcp`
2. Dopo il filtro ridondanza, se `value_type` e' specificato, filtrare:
```python
if value_type:
    enriched = [e for e in enriched if e.get("value_type") == value_type]
```

**Task C2** (15 min):
1. In `audit_workspace_mcp`, dopo aver trovato un match nel registry:
```python
from packaging.version import Version
try:
    local_ver = sv.get("version", "0")
    reg_ver = match.get("version", "0")
    entry["is_outdated"] = Version(reg_ver) > Version(local_ver)
except (AttributeError, ValueError):
    entry["is_outdated"] = None  # non confrontabile
```

**Verifica**:
```bash
uv run python -c "
import asyncio
from mcp_manager.server import server
async def main():
    # Test filtro value_type
    _, data = await server.call_tool('search_useful_mcp', {
        'query': 'postgres', 'value_type': 'database', 'limit': 3
    })
    results = data.get('result', data)
    for r in results:
        assert r.get('value_type') == 'database'
    print(f'OK: {len(results)} risultati filtrati per database')
asyncio.run(main())
"
```

---

### MF 3.2 — Export workspace + Template server (C6 + C4)

**File nuovo**: `src/mcp_manager/templates.json`
**File**: `src/mcp_manager/server.py`

**Task C6** (15 min):
```python
@server.tool(name="export_workspace_mcp", description="Export .mcp.json as readable format")
async def export_workspace(format: str = "markdown") -> str:
    from mcp_manager.utils.config import list_local_servers
    servers = list_local_servers()
    if format == "markdown":
        lines = ["# MCP Workspace Configuration", ""]
        for s in servers:
            lines.append(f"- **{s['name']}**: `{s['command']} {' '.join(s['args'])}`")
        return "\n".join(lines)
    elif format == "json":
        import json
        return json.dumps({"mcpServers": {s["name"]: s for s in servers}}, indent=2)
    return "Unsupported format"
```

**Task C4** (20 min):
```python
# templates.json
{
    "brave-search": {
        "command": "npx",
        "args": ["-y", "@anthropic-ai/mcp-server-brave-search"],
        "env": {"BRAVE_API_KEY": "${BRAVE_API_KEY}"}
    },
    "playwright": {
        "command": "npx",
        "args": ["-y", "@anthropic-ai/mcp-server-playwright"]
    },
    "sentry": {
        "command": "docker",
        "args": ["run", "-i", "--rm", "getsentry/sentry-mcp"]
    }
}
```

**Verifica**:
```bash
uv run python -c "
import asyncio
from mcp_manager.server import server
async def main():
    _, data = await server.call_tool('export_workspace_mcp', {'format': 'markdown'})
    result = data.get('result', data)
    if isinstance(result, str) and len(result) > 10:
        print(f'OK: export {len(result)} chars')
    else:
        print(f'OK (no servers): {result}')
asyncio.run(main())
"
```

---

### MF 3.3 — Rilevamento conflitti + Multi-registry (C3 + C5)

**File**: `src/mcp_manager/server.py` + nuovi

**Task C3** (30 min):
```python
@server.tool(name="detect_conflicts", description="Detect MCP server conflicts")
async def detect_conflicts() -> list[dict]:
    """Check if any two installed MCP servers provide overlapping tool names."""
    from mcp_manager.utils.config import list_local_servers
    servers = list_local_servers()
    # Per ogni server, prova a contattarlo e chiedi listTools
    # (solo server stdio raggiungibili)
    conflicts = []
    # ... logica di rilevamento
    return conflicts
```

**Task C5** (45 min):
1. Creare `src/mcp_manager/utils/smithery.py`:
```python
"""Smithery.ai registry client."""
SMITHERY_API = "https://registry.smithery.ai"

def list_servers(search=None, limit=20):
    # Smithery ha una API diversa dal registry ufficiale
    # Documentazione: https://docs.smithery.ai
    pass
```
2. Aggiungere parametro `registry="official"` a `search_registry`:
```python
async def search_registry(query, limit=20, registry="official"):
    if registry == "smithery":
        return smithery_list(search=query, limit=limit)
    elif registry == "all":
        official = registry_list(search=query, limit=limit)
        smithery = smithery_list(search=query, limit=limit)
        return _merge_dedup(official, smithery)
    return registry_list(search=query, limit=limit)
```

**Verifica**:
```bash
uv run python -c "
import asyncio
from mcp_manager.server import server
async def main():
    _, data = await server.call_tool('detect_conflicts', {})
    print(f'Conflitti: {data}')
asyncio.run(main())
"
```

---

## 📊 Tabella Riepilogativa

| Sprint | MF | Items | Cosa | Sforzo |
|--------|----|-------|------|--------|
| 1 | 1.1 | A4 + A3 | Registry cache + Thread safety | 20 min |
| 1 | 1.2 | A2 | TypedDict types.py | 30 min |
| 1 | 1.3 | A1 | Estrarre tool in 6 moduli | 60 min |
| 1 | 1.4 | A1 fix | Aggiornare test dopo refactoring | 15 min |
| 2 | 2.1 | B1+B3+B2 | Test CLI + prefer_remote + mock | 45 min |
| 2 | 2.2 | B4+B5 | Property-based + 50+ casi ridondanza | 35 min |
| 3 | 3.1 | C1+C2 | Filtro value_type + version audit | 30 min |
| 3 | 3.2 | C6+C4 | Export workspace + template | 35 min |
| 3 | 3.3 | C3+C5 | Conflitti + Multi-registry | 75 min |

**Totale**: 9 microfasi, 15 gap, ~345 min stimati.

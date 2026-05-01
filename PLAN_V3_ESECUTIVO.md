# Piano Esecutivo V3 — MCP Manager

9 items organizzati in 2 Sprint, 7 Microfasi.

---

## 📦 Sprint 1 — Manutenzione + Robustezza (~30 min)

### Microfase 1.1 — Pulizia .gitignore (V1)

**File**: `.gitignore`

**Task**:
1. Rimuovere la riga `_fix_emoji.py` dal `.gitignore` (il file e' gia' stato cancellato)

**Verifica**:
```bash
grep "_fix_emoji" .gitignore
# Output: (nessuna riga)
```

---

### Microfase 1.2 — Test per `fetch_repo_info` + nuovo `test_registry.py` (V2)

**File nuovi/modificati**:
- `tests/test_github.py` — aggiungere test per `fetch_repo_info` con mock
- `tests/test_registry.py` — nuovo file per `list_servers` e `get_server_detail`

**Task**:

1. **Aggiungere a `tests/test_github.py`**:
```python
from unittest.mock import patch, MagicMock
from mcp_manager.utils.github import fetch_repo_info

class TestFetchRepoInfo:
    @patch("httpx.Client")
    def test_successful_fetch(self, mock_client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "stargazers_count": 1000,
            "forks_count": 50,
            "open_issues_count": 5,
            "description": "A test repo",
            "pushed_at": "2026-04-01T00:00:00Z",
            "language": "Python",
            "topics": ["mcp", "testing"],
        }
        mock_resp.headers = {"X-RateLimit-Remaining": "58", "X-RateLimit-Limit": "60"}
        mock_client.return_value.__enter__.return_value.get.return_value = mock_resp
        
        result = fetch_repo_info("https://github.com/owner/repo", force_refresh=True)
        assert result["found"] is True
        assert result["stars"] == 1000
    
    @patch("httpx.Client")
    def test_404(self, mock_client):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_client.return_value.__enter__.return_value.get.return_value = mock_resp
        
        result = fetch_repo_info("https://github.com/owner/missing")
        assert result["found"] is False
    
    def test_non_github_url(self):
        result = fetch_repo_info("https://gitlab.com/owner/repo")
        assert result["found"] is False
        assert "error" in result
    
    def test_cache_hit(self):
        # Chiamata 1: va su GitHub
        result1 = fetch_repo_info("https://github.com/modelcontextprotocol/servers")
        # Chiamata 2: deve usare cache
        result2 = fetch_repo_info("https://github.com/modelcontextprotocol/servers")
        assert result2["found"] is not None  # cache hit, non crash
```

2. **Creare `tests/test_registry.py`**:
```python
"""Test per Registry API client."""
from unittest.mock import patch, MagicMock
from mcp_manager.utils.registry import list_servers, get_server_detail, registry_health

class TestListServers:
    @patch("httpx.Client")
    def test_empty_search(self, mock_client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "servers": [
                {"server": {"name": "test/srv1", "description": "a", "version": "1"}, "_meta": {}},
            ],
            "metadata": {"count": 1, "nextCursor": None},
        }
        mock_client.return_value.__enter__.return_value.get.return_value = mock_resp
        
        results = list_servers(search="test", limit=5)
        assert len(results) == 1
        assert results[0]["name"] == "test/srv1"

    def test_no_results(self):
        results = list_servers(search="xyznonexistent12345", limit=5)
        assert len(results) == 0

class TestGetServerDetail:
    def test_invalid_name(self):
        result = get_server_detail("invalid@name!")
        assert result.get("found") is False
        assert "Invalid" in result.get("error", "")

    def test_nonexistent(self):
        result = get_server_detail("nonexistent.test/server")
        assert result.get("found") is False
```

**Verifica**:
```bash
uv run python -m pytest tests/ -v --tb=short
# Tutti i nuovi test devono passare
```

---

### Microfase 1.3 — `write_mcp_config_entry` con contesto errore (V3)

**File**: `src/mcp_manager/utils/config.py`

**Task**:
1. Avvolgere `find_mcp_config()` in `write_mcp_config_entry()` in try/except
2. Aggiungere contesto all'errore

**Codice**:
```python
def write_mcp_config_entry(...):
    try:
        config_path = find_mcp_config(path)
    except FileNotFoundError:
        raise FileNotFoundError(
            "Cannot write config: no .mcp.json found. "
            "Run from a project directory containing .mcp.json "
            "or set the MCP_CONFIG_PATH environment variable."
        )
```

**Verifica**:
```bash
python -c "
from mcp_manager.utils.config import write_mcp_config_entry
try:
    write_mcp_config_entry('test', {'cmd': 'x'}, path='/nonexistent')
except FileNotFoundError as e:
    print(f'OK: {e}')
"
# Output: OK: Cannot write config: no .mcp.json found. ...
```

---

### Microfase 1.4 — Versionamento `capabilities.json` (V4)

**File**: `src/mcp_manager/data/capabilities.json`
**File**: `src/mcp_manager/utils/capabilities.py`

**Task**:
1. Aggiungere `"version": "2"` in `capabilities.json` > `_meta`:
```json
{
  "_meta": {
    "version": "2",
    "description": "..."
  }
}
```
2. In `_load_capabilities()`, aggiungere check version:
```python
CAPABILITIES_VERSION = 2

def _load_capabilities() -> dict:
    global _caps
    if _caps is not None:
        return _caps
    path = DATA_DIR / "capabilities.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    meta = data.get("_meta", {})
    ver = meta.get("version")
    if ver is not None and ver != CAPABILITIES_VERSION:
        import warnings
        warnings.warn(
            f"capabilities.json version {ver} != expected {CAPABILITIES_VERSION}. "
            "Update expected version in capabilities.py."
        )
    _caps = data
    return _caps
```

**Verifica**:
```bash
python -c "
import warnings
warnings.filterwarnings('error')
from mcp_manager.utils.capabilities import _load_capabilities
c = _load_capabilities()
print(f'OK: version={c[\"_meta\"][\"version\"]}')
"
```

---

## 📦 Sprint 2 — Nuove Feature (~40 min)

### Microfase 2.1 — `ensure_ascii` safe + `GITHUB_CACHE_TTL` (V5 + V7)

**File**: `src/mcp_manager/utils/config.py` (V5)
**File**: `src/mcp_manager/utils/github.py` (V7)

**Task V5**:
1. Cambiare `json.dumps(data, indent=2, ensure_ascii=False)` in `ensure_ascii=True`
2. Aggiungere validazione nomi env var: saltare le chiavi con caratteri non-ASCII

```python
valid_name = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
entry["env"] = {
    ev["name"]: "${" + ev["name"] + "}"
    for ev in env_vars
    if isinstance(ev, dict) and ev.get("name") and valid_name.match(ev["name"])
}
```

**Task V7**:
1. Aggiungere dopo `GITHUB_TIMEOUT`:
```python
CACHE_TTL = int(os.environ.get("GITHUB_CACHE_TTL", "300"))
```
2. La variabile `CACHE_TTL` gia' esiste, va solo resa configurabile

**Verifica**:
```bash
GITHUB_CACHE_TTL=60 python -c "
from mcp_manager.utils.github import CACHE_TTL
assert CACHE_TTL == 60
print(f'OK: CACHE_TTL={CACHE_TTL}')
"
```

---

### Microfase 2.2 — Rate limit reset timestamp (V9)

**File**: `src/mcp_manager/utils/github.py`

**Task**:
1. Aggiungere `_rate_limit_reset: int | None = None` dopo `_rate_limit_limit`
2. Nella sezione di tracking response headers:
```python
reset = resp.headers.get("X-RateLimit-Reset")
if reset is not None:
    _rate_limit_reset = int(reset)
```
3. Aggiornare `get_rate_limit_status()`:
```python
def get_rate_limit_status() -> dict:
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
```
4. Nel warning in `server.py:_attach_rate_warning()`, aggiornare messaggio:
```python
if rl.get("resets_in_minutes"):
    msg = (
        f"GitHub API rate limit basso: {rl['remaining']}/{rl['limit']} richieste. "
        f"Resetta tra ~{rl['resets_in_minutes']}min. "
        "Imposta GITHUB_TOKEN per 5.000 req/h."
    )
```

**Verifica**:
```bash
python -c "
from mcp_manager.utils.github import get_rate_limit_status
s = get_rate_limit_status()
print(f'resets_in_seconds={s[\"resets_in_seconds\"]}')
# Output: resets_in_seconds=<num> oppure None
"
```

---

### Microfase 2.3 — CLI flag + GitHub Actions CI (V6 + V8)

**File**: `src/mcp_manager/server.py` (V6)
**File nuovo**: `.github/workflows/test.yml` (V8)

**Task V6**:
1. Aggiungere `argparse` in `main()`:
```python
import argparse

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MCP Manager — discover, evaluate, and manage MCP servers",
    )
    parser.add_argument(
        "--version", action="version",
        version=f"mcp-manager v{__version__}",
    )
    parser.add_argument(
        "--http", action="store_true",
        help="Run as HTTP server instead of stdio",
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help="HTTP port (default: 8000)",
    )
    args = parser.parse_args()
    
    if args.http:
        server.run(host="0.0.0.0", port=args.port)
    else:
        server.run()
```
2. Aggiungere `__version__` import:
```python
from mcp_manager import __version__
```

**Task V8**:
1. Creare `export PATH`-aware workflow:
```yaml
# .github/workflows/test.yml
name: Test
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v5
      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}
      - name: Install dependencies
        run: uv sync --dev
      - name: Run tests
        run: uv run python -m pytest tests/ -v --tb=short
      - name: Smoke test (no network)
        run: uv run python scripts/smoke_test.py || echo "Smoke test requires network - skipped"
```

**Verifica CLI**:
```bash
python -m mcp_manager --help
# Mostra help
python -m mcp_manager --version
# Output: mcp-manager v0.3.0
```

**Verifica CI**: Push su GitHub → Actions tab → workflow visibile.

---

## 📊 Riepilogo Sprint

| Sprint | Microfase | Items | Sforzo |
|--------|-----------|-------|--------|
| **Sprint 1** | 1.1 → 1.2 → 1.3 → 1.4 | V1, V2, V3, V4 | ~30 min |
| **Sprint 2** | 2.1 → 2.2 → 2.3 | V5, V7, V9, V6, V8 | ~40 min |
| **Totale** | 7 microfasi | 9 items | ~70 min |

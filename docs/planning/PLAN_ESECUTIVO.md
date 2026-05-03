# Piano Esecutivo — MCP Manager Fixes v2

13 items organizzati in 3 Sprint, 9 Microfasi.

---

## 📦 Sprint 1 — Bugfix Urgenti (4 microfasi)

### Microfase 1.1 — `GITHUB_TIMEOUT` configurabile (B4)

**File**: `src/mcp_manager/utils/github.py`

**Task**:
1. Aggiungere `GITHUB_TIMEOUT = int(os.environ.get("GITHUB_TIMEOUT", "15"))` dopo `CACHE_TTL`
2. Sostituire `timeout=15` con `timeout=GITHUB_TIMEOUT` nella chiamata `client.get()` (riga ~85)
3. Sostituire `timeout=10` con `timeout=GITHUB_TIMEOUT` nel blocco `try/except` della `registry_health`-style... no, quello è in registry.py. In github.py c'è solo `timeout=15`.

**Verifica**:
```bash
GITHUB_TIMEOUT=5 python -c "from mcp_manager.utils.github import fetch_repo_info; print('OK')"
```

---

### Microfase 1.2 — Rimuovere emoji dai label (B5)

**File**: `src/mcp_manager/utils/capabilities.py` (VALUE_CLASSIFICATION)
**File**: `src/mcp_manager/data/capabilities.json` (categorie)

**Task**:
1. Sostituire label con emoji in `capabilities.py`:
   - `"🗄️  Database"` → `"[DB] Database"`
   - `"☁️  Cloud / DevOps"` → `"[Cloud] Cloud/DevOps"`
   - `"📋  Project Mgmt"` → `"[PM] Project Mgmt"`
   - `"💬  Communication"` → `"[Chat] Communication"`
   - `"📊  Monitoring"` → `"[Mon] Monitoring"`
   - `"🎨  Design"` → `"[Design] Design"`
   - `"💰  Payments"` → `"[$] Payments"`
   - `"🎬  Media"` → `"[Media] Media"`
   - `"📍  Geolocation"` → `"[Geo] Geolocation"`
   - `"📊  Analytics / BI"` → `"[BI] Analytics/BI"`
   - `"🤖  AI / ML"` → `"[AI] AI/ML"`
   - `"🛒  E-commerce / CMS"` → `"[Shop] E-commerce/CMS"`
   - `"🔴  Ridondante (già in pi)"` → `"[RED] Ridondante"`
   - `"📦  Generico"` → `"[Gen] Generico"`
2. Stessa operazione in `data/capabilities.json` per tutti i `"label"` fields

**Verifica**:
```bash
python -c "
from mcp_manager.utils.capabilities import classify_value
v = classify_value('test/server', 'PostgreSQL database')
print(v['value_label'])  # deve essere [DB] Database, senza emoji
"
```

---

### Microfase 1.3 — Dead code: esporre o rimuovere (B6)

**File**: `src/mcp_manager/server.py` (import)
**File**: `src/mcp_manager/utils/capabilities.py` (funzione)

**Task**:
Opzione A (consigliata): Creare un nuovo tool `pi_capabilities` che espone la mappa:
```python
@server.tool(
    name="pi_capabilities",
    description="Mostra quali capacità ha già pi/Craft Agents built-in. "
    "Utile per capire se un MCP server è ridondante prima di installarlo.",
)
async def pi_caps() -> str:
    """Return markdown summary of pi built-in capabilities."""
    return get_redundancy_help()
```

**Verifica**: Il tool `pi_capabilities` appare nella lista strumenti.

---

### Microfase 1.4 — Aggiungere type hints mancanti (M7)

**File**: `src/mcp_manager/server.py`

**Task**: Aggiungere return type alle funzioni che mancano:
- `list_local()` → `-> list[dict[str, Any]]`
- `trust_assessment()` → `-> dict[str, Any]`
- `health_check()` → `-> dict[str, Any]`
- `pi_caps()` (se creata) → `-> str`
- `_attach_rate_warning()` → `-> None`
- `main()` → `-> None`

**Verifica**:
```bash
python -c "
import ast, sys
with open('src/mcp_manager/server.py') as f:
    tree = ast.parse(f.read())
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.returns is None:
        if not node.name.startswith('_'):  # skip private
            print(f'MISSING: {node.name}')
"
```

---

## 📦 Sprint 2 — Igiene Repository (3 microfasi)

### Microfase 2.1 — Versione e metadata (E8)

**File**: `pyproject.toml`
**File nuovo**: `src/mcp_manager/__init__.py`

**Task**:
1. `pyproject.toml`: `version = "0.3.0"`
2. `src/mcp_manager/__init__.py`:
   ```python
   __version__ = "0.3.0"
   ```
3. `pyproject.toml`: aggiungere `__version__` link:
   ```toml
   [tool.setuptools.dynamic]
   version = {attr = "mcp_manager.__version__"}
   ```

**Verifica**:
```bash
python -c "from mcp_manager import __version__; print(__version__)"
# Output: 0.3.0
```

---

### Microfase 2.2 — SKILL.md aggiornata (E9)

**File**: `SKILL.md`

**Task**: Aggiungere:
- Tool mancante `search_useful_mcp` con descrizione
- Tool mancante `pi_capabilities` (se creata)
- Nuovi score: `redundancy_score`, `value_score`, `composite_score`
- Filtro `include_redundant` e `filter_untrusted`

**Verifica**: Lettura visiva, controllo che tutti i 10-11 tool siano documentati.

---

### Microfase 2.3 — .gitignore e py.typed (M11 + M12)

**File**: `.gitignore`
**File nuovo**: `src/mcp_manager/py.typed`

**Task**:
1. Aggiungere a `.gitignore`:
   ```
   # Build artifacts
   *.egg-info/
   dist/
   build/
   
   # IDE
   .vscode/
   .idea/
   ```
2. Creare `src/mcp_manager/py.typed` (file vuoto, marcatore PEP 561)

**Verifica**:
```bash
test -f src/mcp_manager/py.typed && echo "OK"
```

---

## 📦 Sprint 3 — Qualità e Robustezza (2 microfasi)

### Microfase 3.1 — Test automatici con pytest (E7 + M10)

**File nuovi**: `tests/test_capabilities.py`, `tests/test_github.py`, `tests/test_config.py`, `tests/test_server.py`, `scripts/smoke_test.py`
**File**: `pyproject.toml` (aggiungere dev-dependencies)

**Task**:

1. Creare `tests/test_capabilities.py`:
```python
"""Unit test per redundancy e value scoring."""
from mcp_manager.utils.capabilities import (
    compute_redundancy, classify_value, compute_composite_score,
)

class TestRedundancy:
    def test_filesystem_is_redundant(self):
        r = compute_redundancy("io.github.x/filesystem", "filesystem access")
        assert r["redundant"] is True

    def test_kubernetes_not_redundant(self):
        r = compute_redundancy("io.github.containers/kubernetes", "K8s management")
        assert r["redundant"] is False

    def test_semantic_code_search_not_redundant(self):
        r = compute_redundancy("io.github.x/code-search", "Semantic code search")
        assert r["redundant"] is False

class TestCompositeScore:
    def test_all_zero(self):
        assert compute_composite_score(0, 0, 0) == 0.0

    def test_max(self):
        assert compute_composite_score(100, 0, 100) == 100.0

class TestValueClassification:
    def test_database(self):
        v = classify_value("test/pg", "PostgreSQL database")
        assert v["value_type"] == "database"

    def test_multi_label(self):
        v = classify_value("test/multi", "PostgreSQL on Kubernetes with monitoring")
        assert len(v.get("value_types", [])) >= 2
```

2. Creare `tests/test_github.py`:
```python
from mcp_manager.utils.github import compute_trust_score, _parse_github_repo

class TestParseRepo:
    def test_standard_url(self):
        assert _parse_github_repo("https://github.com/owner/repo") == ("owner", "repo")
    
    def test_git_suffix(self):
        assert _parse_github_repo("https://github.com/owner/repo.git") == ("owner", "repo")

    def test_non_github(self):
        assert _parse_github_repo("https://gitlab.com/owner/repo") is None

class TestTrustScore:
    def test_high_trust(self):
        s = compute_trust_score({"found": True, "stars": 1000, "forks": 100, "days_since_update": 5})
        assert s["is_trusted"] is True
        assert s["trust_score"] == 100.0

    def test_zero(self):
        s = compute_trust_score({"found": True, "stars": 0, "forks": 0, "days_since_update": 999})
        assert s["trust_score"] == 0.0
```

3. Creare `tests/test_config.py`:
```python
import tempfile, json, os
from pathlib import Path
from mcp_manager.utils.config import find_mcp_config, list_local_servers, read_mcp_config

class TestConfig:
    def test_no_config_returns_empty(self):
        assert list_local_servers("/nonexistent") == []

    # ... altri test
```

4. Creare `scripts/smoke_test.py`:
```python
"""Smoke test: verifica che tutti i tool rispondano senza crash."""
import asyncio, sys
from mcp_manager.server import server

async def smoke():
    tools = await server.list_tools()
    print(f"✅ {len(tools)} tools registrati")
    
    # Test tool senza rete
    _, data = await server.call_tool("registry_health", {})
    assert data.get("reachable") is not None
    print(f"✅ registry_health: OK")
    
    for name in ["list_local_servers"]:
        _, data = await server.call_tool(name, {})
        print(f"✅ {name}: OK")

asyncio.run(smoke())
```

5. Aggiungere a `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]

[project.optional-dependencies]
dev = ["pytest>=8.0"]
```

**Verifica**:
```bash
uv sync --dev
uv run pytest tests/ -v
# Output: tutti PASS
```

---

### Microfase 3.2 — packages+remotes misti + API version-aware (E6 + M8)

**File**: `src/mcp_manager/server.py` (E6)
**File**: `src/mcp_manager/utils/registry.py` (M8)

**Task E6**:
1. Aggiungere parametro `prefer_remote: bool = False` a `generate_mcp_config`
2. Se `prefer_remote=True` e ci sono remotes, usare quelli invece di packages
3. Nel risultato, includere `also_available_as_remote: bool` se esistono entrambi

**Task M8**:
1. Aggiungere `REGISTRY_API_VERSION = os.environ.get("REGISTRY_API_VERSION", "v0.1")`
2. Usarla in tutti gli URL invece di `v0.1` hardcoded
3. Aggiornare anche i path `/v0/` (auth endpoints) se presenti

**Verifica**:
```python
# E6
from mcp_manager.server import gen_config
# (test con un server che ha sia packages che remotes)

# M8
REGISTRY_API_VERSION=v1.0 python -c "from mcp_manager.utils.registry import list_servers; print('OK')"
```

---

## 📊 Riepilogo Sprint

| Sprint | Microfasi | Items | Sforzo stimato |
|--------|-----------|-------|----------------|
| **Sprint 1** | 1.1 → 1.2 → 1.3 → 1.4 | B4, B5, B6, M7 | ~25 min |
| **Sprint 2** | 2.1 → 2.2 → 2.3 | E8, E9, M11, M12 | ~20 min |
| **Sprint 3** | 3.1 → 3.2 | E7, M10, E6, M8 | ~90 min |

**Totale**: 9 microfasi in 3 sprint, ~135 minuti stimati.

# Piano V5 — Migliorie Sostanziali

Analisi approfondita: 2.123 linee, 33 funzioni, 0 classi, 5 moduli.
Identificati **15 gap** organizzati in 3 aree strategiche.

---

## 🏗️ Area 1 — Refactoring Architetturale (4 items)

### A1. Estrarre i tool da `server.py` in moduli separati

**Problema**: `server.py` = 619 linee, 16 funzioni, 11 tool. Viola Single Responsibility Principle.

**Soluzione**: Creare `src/mcp_manager/tools/` con:
```
tools/
  __init__.py     # Tool registry helper
  local.py        # list_local_servers
  registry.py     # search_registry, get_server_details, registry_health
  trust.py        # assess_trustworthiness
  search.py       # search_trusted, search_useful_mcp
  compare.py      # compare_alternatives
  config.py       # generate_mcp_config
  audit.py        # audit_workspace_mcp, pi_capabilities
```

**Vantaggio**: Ogni file < 100 linee. Manutenibilita radicalmente migliorata.

---

### A2. Tipizzare i ritorni con `TypedDict` / `dataclass`

**Problema**: Le funzioni ritornano `dict[str, Any]` — niente type checking sui campi.

**Soluzione**: Creare `src/mcp_manager/types.py`:
```python
from typing import TypedDict, NotRequired

class ServerInfo(TypedDict):
    name: str
    version: str
    description: str
    status: str

class TrustScore(TypedDict):
    trust_score: float
    is_trusted: bool
    stars_score: float
    recency_score: float
    forks_score: float
    warnings: list[str]

class EnrichedServer(ServerInfo):
    trust_score: float
    composite_score: float
    redundancy_score: int
    value_score: int
    value_label: str
    value_types: list[str]
```

**Vantaggio**: Type checking statico, autocompletamento IDE, auto-documentazione.

---

### A3. Rendere thread-safe le variabili globali

**Problema**: `github.py` usa 3 variabili mutabili a livello di modulo (`_rate_limit_*`). In un server multi-thread, ci sarebbero race condition.

**Soluzione**: Usare `threading.Lock` o spostare lo stato in un oggetto `RateLimitTracker`.

---

### A4. Aggiungere cache per Registry API

**Problema**: Solo GitHub ha cache. Le chiamate al Registry non sono cached.

**Soluzione**: Aggiungere `_registry_cache: dict[str, tuple[float, Any]]` in `registry.py` con TTL configurabile via `REGISTRY_CACHE_TTL`.

---

## 🧪 Area 2 — Test e Qualita (5 items)

### B1. Test per CLI argument parsing

**File nuovo**: `tests/test_cli.py`
```python
class TestCLI:
    def test_version_flag(self):
        # python -m mcp_manager --version
        result = subprocess.run([sys.executable, '-m', 'mcp_manager', '--version'], ...)
        assert result.returncode == 0
        assert 'v0.4.0' in result.stdout
```

---

### B2. Integration test con mock del Registry API

**File**: `tests/test_registry.py` — aggiungere test con `responses` o `pytest-httpx`.

```python
@patch('mcp_manager.utils.registry.httpx.Client')
def test_list_with_mock(self, mock_client):
    mock_client.return_value.__enter__.return_value.get.return_value = ...
```

---

### B3. Test per `gen_config` con `prefer_remote=True`

**File**: `tests/test_server.py`

```python
def test_gen_config_prefer_remote(self):
    text, data = asyncio.run(server.call_tool('generate_mcp_config', {
        'server_name': '...',
        'prefer_remote': True,
    }))
    assert 'url' in data.get('result', data).get('new_entry', {})
```

---

### B4. Property-based test per `compute_trust_score`

Usare `hypothesis` per generare input casuali e verificare che:
- trust_score sia sempre 0-100
- is_trusted sia True solo se score >= 50
- warnings non contengano falsi positivi

---

### B5. Test per `compute_redundancy` con 100+ casi

Aggiungere una batteria di test automatizzata con 100+ combinazioni di nome/descrizione per garantire che non ci siano regressioni nella classificazione ridondanza.

---

## 🚀 Area 3 — Nuove Funzionalita (6 items)

### C1. Filtro per `value_type` in `search_useful_mcp`

**Problema**: `search_useful_mcp` filtra i ridondanti ma non permette di cercare per categoria specifica.

**Soluzione**: Aggiungere parametro `value_type: str = ""`:
```
search_useful_mcp(query="postgres", value_type="database")
```
Se specificato, filtra i risultati mostrando solo quelli con quel value_type.

---

### C2. Confronto versioni in `audit_workspace_mcp`

**Problema**: `is_outdated` e' sempre `False` perche' non c'e' logica di confronto.

**Soluzione**: Aggiungere `packaging.version` per confrontare versioni semver:
```python
from packaging.version import Version
try:
    is_outdated = Version(local_ver) < Version(registry_ver)
except:
    is_outdated = None  # versione non confrontabile
```

---

### C3. Rilevamento conflitti tool MCP

**Problema**: Se due MCP server registrano lo stesso tool name, l'utente non viene avvisato.

**Soluzione**: Nuovo tool `detect_conflicts()` che controlla se due server MCP installati offrono tool con lo stesso nome.

---

### C4. Template per server popolari

**Problema**: `generate_mcp_config` parte da zero per ogni server. Nessun template preimpostato.

**Soluzione**: Aggiungere `templates.json` con configurazioni precompilate per server noti (Brave Search, Sentry, Playwright, etc.).

---

### C5. Multi-registry support (Smithery)

**Problema**: Il tool cerca solo su `registry.modelcontextprotocol.io`. Smithery.ai e' il secondo registry MCP piu' grande.

**Soluzione**: Aggiungere parametro `registry="official"` o `registry="smithery"` a `search_registry`. Bonus: `registry="all"` per cercare su entrambi.

---

### C6. `export_workspace_mcp` tool

**Problema**: Nessun modo per esportare la configurazione MCP in formato portabile.

**Soluzione**: Nuovo tool che esporta `.mcp.json` in formato README o JSON leggibile.

---

## 📊 Tabella Impatto/Sforzo

| ID | Area | Cosa | Sforzo | Impatto |
|----|------|------|--------|---------|
| A1 | Arch | Estrarre tool in moduli separati | 60min | 🔴 Alto |
| A2 | Arch | TypedDict per i tipi | 30min | 🟡 Medio |
| A3 | Arch | Thread safety globals | 15min | 🟢 Basso |
| A4 | Arch | Registry cache | 10min | 🟢 Basso |
| B1 | Test | Test CLI | 15min | 🟡 Medio |
| B2 | Test | Mock integration test | 20min | 🟡 Medio |
| B3 | Test | Test gen_config prefer_remote | 10min | 🟡 Medio |
| B4 | Test | Property-based test | 20min | 🟢 Basso |
| B5 | Test | Battery 100+ test ridondanza | 15min | 🟡 Medio |
| C1 | Feat | Filtro value_type | 15min | 🟡 Medio |
| C2 | Feat | Confronto versioni audit | 15min | 🟡 Medio |
| C3 | Feat | Rilevamento conflitti | 30min | 🟡 Medio |
| C4 | Feat | Template server popolari | 20min | 🟢 Basso |
| C5 | Feat | Multi-registry | 45min | 🔴 Alto |
| C6 | Feat | Export workspace | 15min | 🟢 Basso |

---

## 🚀 Sprint consigliati

```
Sprint 1 (Architettura, ~115min):
  A4 -> A3 -> A2 -> A1

Sprint 2 (Qualita, ~80min):
  B3 -> B1 -> B2 -> B4 -> B5

Sprint 3 (Feature, ~140min):
  C1 -> C2 -> C6 -> C4 -> C3 -> C5
```

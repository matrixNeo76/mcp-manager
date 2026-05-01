# Piano di Miglioramento v2 — MCP Manager

Analisi approfondita dopo 4 round di sviluppo. 1685 linee di codice, 10 tool, 4 moduli utility.

---

## 🔴 BUG — Priorità Alta

### B4. `github.py` timeout hardcoded (2 occorrenze)

**File**: `src/mcp_manager/utils/github.py:85` e `:126`

**Problema**: `timeout=15` e `timeout=10` hardcoded. Manca `GITHUB_TIMEOUT` env var come già fatto per `REGISTRY_TIMEOUT`.

**Fix**: Sostituire con `int(os.environ.get("GITHUB_TIMEOUT", "15"))`.

---

### B5. Emoji nei label causano crash su terminali Windows cp1252

**File**: `src/mcp_manager/utils/capabilities.py` (VALUE_CLASSIFICATION labels)
**File**: `src/mcp_manager/server.py` (descrizioni con emoji)

**Problema**: Le emoji (🗄️, ☁️, 📋, 💬, 📊, 🎨, 💰, 🎬, 📍, 🛒, 🔴) causano `UnicodeEncodeError` su terminali Windows che usano codepage cp1252.

**Fix**: Sostituire tutte le emoji con equivalenti ASCII: `[DB]`, `[Cloud]`, `[PM]`, `[Chat]`, `[Mon]`, `[Design]`, `[$]`, `[Media]`, `[Geo]`, `[Ecom]`, `[RED]`.

---

### B6. `get_redundancy_help` importata ma mai esposta come tool

**File**: `src/mcp_manager/server.py:26`

**Problema**: `get_redundancy_help()` è importata da capabilities.py ma non è MAI chiamata da nessun tool. È dead code.

**Fix**: Creare un tool `pi_capabilities` che espone questa funzione, oppure rimuovere l'import e la funzione se non serve.

---

## 🟡 PRIORITÀ MEDIA

### E6. `generate_mcp_config` non gestisce packages+remotes insieme

**File**: `src/mcp_manager/server.py:296-370`

**Problema**: Se un server ha SIA packages CHE remotes, il codice processa solo packages. L'utente non vede che esiste anche una versione remote.

**Fix**: Aggiungere opzione `prefer_remote=False` e/o mostrare entrambe le opzioni nel risultato.

---

### E7. Test automatici assenti

**Problema**: Non esiste una directory `tests/`. Tutti i test sono stati eseguiti manualmente via `python -c`.

**Fix**: Creare test con pytest:
- `tests/test_capabilities.py` — unit test per redundancy e value scoring
- `tests/test_github.py` — unit test per trust score e URL parsing
- `tests/test_config.py` — unit test per lettura/scrittura .mcp.json
- `tests/test_registry.py` — integration test per API (mockata)
- `tests/test_server.py` — integration test per tool registration

---

### E8. Versionamento fermo a 0.2.0

**File**: `pyproject.toml`

**Problema**: Dopo 4 commit di fix sostanziali (3 bug + 5 edge + 6 migliorie), la versione è ancora 0.2.0.

**Fix**: Aggiornare a 0.3.0 e aggiungere versione in `__init__.py`:
```python
__version__ = "0.3.0"
```

---

### E9. SKILL.md non aggiornata

**File**: `SKILL.md`

**Problema**: Manca `search_useful_mcp` e i nuovi score (composite, redundancy, value).

**Fix**: Aggiungere documentazione per tutti i tool e score.

---

## 🟢 MIGLIORIE — Priorità Bassa

### M7. Aggiungere tipo di ritorno mancante in server.py

**File**: `src/mcp_manager/server.py`

**Problema**: Alcune funzioni async non hanno return type hint.

**Fix**: Aggiungere `-> list[dict[str, Any]]` e `-> dict[str, Any]` ovunque manchino.

---

### M8. Registry API version-aware

**File**: `src/mcp_manager/utils/registry.py`

**Problema**: API URL hardcoded a `/v0.1/`. Se il registry passa a `/v1.0/`, tutto si rompe.

**Fix**: Estrarre la versione da `get_server_detail` e usarla come base. Oppure aggiungere `REGISTRY_API_VERSION` env var.

---

### M9. Rate limiting lato client per GitHub

**File**: `src/mcp_manager/utils/github.py`

**Problema**: Nessun rate limiting client-side — `asyncio.gather` con semaforo(5) protegge parzialmente, ma non c'è backoff in caso di 429/403.

**Fix**: Implementare exponential backoff su 403/429 e/salvare il rate limit reset timestamp.

---

### M10. Test di integrazione end-to-end

**Problema**: Nessuna garanzia che i tool funzionino contro API reali.

**Fix**: Script di smoke test in `scripts/smoke_test.py` che testa ogni tool contro API reali.

---

### M11. .gitignore per egg-info e build artifacts

**File**: `.gitignore`

**Problema**: `*.egg-info/` e `dist/` non sono gitignorati. `uv build` potrebbe generare artefatti.

**Fix**: Aggiungere `*.egg-info/`, `dist/`, `build/` a `.gitignore`.

---

### M12. Aggiungere `py.typed` per typing PEP 561

**Problema**: Il pacchetto manca del marker `py.typed` per la compatibilità con mypy/pyright strict mode.

**Fix**: Creare `src/mcp_manager/py.typed` (file vuoto).

---

## 📊 Tabella

| ID | Tipo | Cosa | Sforzo | File |
|----|------|------|--------|------|
| B4 | Bug | github.py timeout hardcoded | 5min | github.py |
| B5 | Bug | Emoji crash cp1252 | 10min | capabilities.py, server.py |
| B6 | Bug | get_redundancy_help dead code | 5min | server.py |
| E6 | Edge | packages+remotes misti | 15min | server.py |
| E7 | Edge | Test assenti | 60min | tests/ |
| E8 | Edge | Versione ferma a 0.2.0 | 2min | pyproject.toml |
| E9 | Edge | SKILL.md non aggiornata | 10min | SKILL.md |
| M7 | Miglioria | Return type hints | 5min | server.py |
| M8 | Miglioria | API version-aware | 15min | registry.py |
| M9 | Miglioria | Client rate limiting | 20min | github.py |
| M10 | Miglioria | Smoke test | 20min | scripts/ |
| M11 | Miglioria | .gitignore lacune | 2min | .gitignore |
| M12 | Miglioria | py.typed marker | 1min | src/mcp_manager/ |

---

## 🚀 Ordine Sprint

```
Sprint 1 (bugfix urgenti):
  B4 → B5 → B6 → M7

Sprint 2 (igiene repo):
  E8 → E9 → M11 → M12 → E6

Sprint 3 (qualità):
  E7 → M10 → M8 → M9
```

# Piano di Miglioramento v3 — MCP Manager

Analisi approfondita della codebase v0.3.0: 2.288 linee, 13 file Python, 62 test, 11 tool.

---

## Riepilogo analisi

Nessun bug critico trovato. Tutti gli edge case gestiti correttamente (input vuoti, stringhe enormi, input non validi). 62 test passano. 3 chiamate concorrenti senza crash.

Trovati **9 items** tra manutenzione, robustezza e migliorie.

---

## 🟡 Priorità Media (4 items)

### V1. `_fix_emoji.py` rimosso dal repo ma ancora in `.gitignore`

**File**: `.gitignore`

**Problema**: `_fix_emoji.py` è elencato nel `.gitignore` come file temporaneo — ma l'abbiamo già cancellato. L'entry è residua.

**Fix**: Rimuovere la riga `_fix_emoji.py` dal `.gitignore`.

---

### V2. Test dedicated per `fetch_repo_info()` e `list_servers()`

**File**: `tests/test_github.py`, `tests/test_registry.py` (nuovo)

**Problema**: `fetch_repo_info()` fa chiamate HTTP reali e non ha test unitari (solo `compute_trust_score` e `_parse_github_repo` sono testati). `list_servers()` non ha test.

**Fix**:
- `test_github.py`: Mockare httpx per testare `fetch_repo_info()` con risposte simulate
- Nuovo `tests/test_registry.py`: Testare `list_servers()` con mock della registry API

---

### V3. `write_mcp_config_entry` senza `.mcp.json` si blocca

**File**: `src/mcp_manager/utils/config.py:68`

**Problema**: Se si chiama `write_mcp_config_entry()` in una directory senza `.mcp.json`, il `find_mcp_config()` interno solleva `FileNotFoundError` senza un messaggio utile che spieghi *cosa* stava tentando di fare.

**Fix**: Avvolgere in try/except e aggiungere contesto:
```python
try:
    config_path = find_mcp_config(path)
except FileNotFoundError:
    raise FileNotFoundError(
        "Cannot write config: no .mcp.json found. "
        "Run from a project directory with .mcp.json or set MCP_CONFIG_PATH."
    )
```

---

### V4. Versionamento `capabilities.json`

**File**: `src/mcp_manager/data/capabilities.json`

**Problema**: Il file non ha versione. Se qualcuno modifica il JSON, non c'e' modo di sapere se e' aggiornato.

**Fix**: Aggiungere `"version": "2"` nel `_meta` e verificarlo in `_load_capabilities()` con warning se la versione e' cambiata.

---

## 🟢 Priorità Bassa (5 items)

### V5. `ensure_ascii=False` in `write_mcp_config_entry`

**File**: `src/mcp_manager/utils/config.py:83`

**Problema**: `ensure_ascii=False` permette caratteri non-ASCII nei file `.mcp.json` generati. Se un env var name contiene Unicode, si scrive Unicode.

**Fix**: Cambiare in `ensure_ascii=True` (safe default) o validare i nomi delle env var prima di scrivere.

---

### V6. Nessun `--help` o CLI flag

**File**: `src/mcp_manager/server.py`

**Problema**: `mcp-manager` parte direttamente senza supporto per `--help`, `--version`, `--port`.

**Fix**: Aggiungere `argparse` per:
```
mcp-manager                    # Avvia server stdio
mcp-manager --http --port 9999 # Avvia server HTTP
mcp-manager --version          # Stampa versione
mcp-manager --help             # Stampa help
```

---

### V7. Configurabilità della cache TTL

**File**: `src/mcp_manager/utils/github.py:25`

**Problema**: `CACHE_TTL = 300` hardcoded (5 minuti). Chi vuole una cache piu' breve o piu' lunga non puo' configurarla.

**Fix**: `CACHE_TTL = int(os.environ.get("GITHUB_CACHE_TTL", "300"))`

---

### V8. Nessuna integrazione CI

**Problema**: Il repo non ha GitHub Actions. Ogni commit richiede test manuali.

**Fix**: Aggiungere `.github/workflows/test.yml`:
```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run python -m pytest tests/ -v
```

---

### V9. Rate limit reset timestamp

**File**: `src/mcp_manager/utils/github.py`

**Problema**: Il sistema traccia `X-RateLimit-Remaining` ma non `X-RateLimit-Reset`, quindi non si sa *quando* verra' azzerato il limite.

**Fix**: Aggiungere `_rate_limit_reset` e calcolare `resets_in_seconds`. Includere nel warning:
```
GitHub API rate limit: 3/60 remaining. Resets in 47 minutes.
```

---

## 📊 Tabella riassuntiva

| ID | Tipo | Cosa | Sforzo | Impatto |
|----|------|------|--------|---------|
| V1 | Manut | `_fix_emoji.py` residuo in `.gitignore` | 1min | Basso |
| V2 | Test | Test per `fetch_repo_info` + `list_servers` | 20min | Medio |
| V3 | Rob | `write_mcp_config_entry` + contesto errore | 5min | Medio |
| V4 | Manut | `capabilities.json` versionato | 5min | Basso |
| V5 | Rob | `ensure_ascii` safe | 5min | Basso |
| V6 | Migl | CLI flag (--help, --version, --http) | 15min | Medio |
| V7 | Migl | `GITHUB_CACHE_TTL` env var | 2min | Basso |
| V8 | Migl | GitHub Actions CI | 10min | Alto |
| V9 | Migl | Rate limit reset timestamp | 10min | Basso |

**Totale**: 9 items, ~73 minuti stimati.

---

## Sprint consigliati

```
Sprint 1 (manutenzione + robustezza, ~30min):
  V1 -> V2 -> V3 -> V4 -> V5

Sprint 2 (nuove feature, ~40min):
  V7 -> V9 -> V6 -> V8
```

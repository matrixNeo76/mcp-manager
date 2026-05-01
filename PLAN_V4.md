# Piano di Miglioramento v4 — MCP Manager

Analisi: 2.463 linee, 70 test, 11 tool, 9 commit su main.

---

## 🔴 Bug (3)

### W1. `prefer_remote` non nella firma di `gen_config`

**File**: `src/mcp_manager/server.py:292`

**Problema**: Il parametro `prefer_remote` e' usato nel corpo della funzione (L309) ma non e' mai stato aggiunto alla firma `async def gen_config(...)`. FastMCP non lo vede, quindi il tool non accetta il parametro.

**Fix**: Aggiungere `prefer_remote: bool = False` alla firma della funzione.

---

### W2. `--help` mostra `__main__.py` invece di `mcp-manager`

**File**: `src/mcp_manager/server.py:560`

**Problema**: `argparse` usa `sys.argv[0]` come nome programma. Con `python -m mcp_manager`, argv[0] = `__main__.py`.

**Fix**: Aggiungere `prog="mcp-manager"` al `ArgumentParser`.

---

### W3. CLI `--http` non funziona

**File**: `src/mcp_manager/server.py:578`

**Problema**: `server.run(host=..., port=...)` usa la configurazione HTTP di FastMCP, ma il server MCP richiede piu' setup per l'HTTP (endpoint /mcp, SSE). Il server parte ma non risponde alle richieste.

**Fix**: Verificare la firma di `FastMCP.run()`. Se non supporta host/port, documentare che `--http` e' sperimentale o rimuovere il flag.

---

## 🟡 Priorita Media (3)

### W4. `GITHUB_CACHE_TTL` non documentato in README

**File**: `README.md`

**Problema**: La variabile d'ambiente `GITHUB_CACHE_TTL` esiste nel codice ma non e' documentata nella tabella delle env var del README.

**Fix**: Aggiungere riga alla tabella delle environment variables.

---

### W5. CRLF/LF misti

**File**: `src/mcp_manager/server.py`, `src/mcp_manager/utils/capabilities.py`

**Problema**: server.py e capabilities.py usano CRLF (Windows), gli altri file usano LF (Unix). Git mostra warning a ogni commit.

**Fix**: Convertire a LF con `sed` o `dos2unix`.

---

### W6. Nessun `__all__` in `__init__.py`

**File**: `src/mcp_manager/__init__.py`

**Problema**: Manca `__all__`, quindi `from mcp_manager import *` esporta tutto.

**Fix**: Aggiungere `__all__ = ["__version__"]`.

---

## 🟢 Priorita Bassa (3)

### W7. `.gitignore` non copre `scripts/` e `tests/` .pyc

**File**: `.gitignore`

**Problema**: `__pycache__/` e' coperto, ma se qualcuno esegue `pytest` dalla root, i `.pyc` in `tests/` e `scripts/` non sono esclusi esplicitamente.

**Fix**: Aggiungere `tests/__pycache__/` e `scripts/__pycache__/`.

---

### W8. Versione 0.4.0

**File**: `pyproject.toml`, `src/mcp_manager/__init__.py`, `CHANGELOG.md`

**Problema**: Dopo 2 round di fix, la versione e' ancora 0.3.0.

**Fix**: Bump a 0.4.0 + aggiungere sezione v0.4.0 in CHANGELOG.

---

### W9. CLI help non mostra default values

**File**: `src/mcp_manager/server.py`

**Problema**: `--help` mostra `--port PORT` e `--host HOST` senza far vedere i default.

**Fix**: Aggiungere `metavar` o usare `%default` nelle descrizioni.

---

## 📊 Tabella

| ID | Tipo | Cosa | Sforzo | File |
|----|------|------|--------|------|
| W1 | Bug | `prefer_remote` non in firma | 2 min | server.py |
| W2 | Bug | `--help` mostra `__main__.py` | 1 min | server.py |
| W3 | Bug | `--http` non funziona | 10 min | server.py |
| W4 | Doc | `GITHUB_CACHE_TTL` in README | 2 min | README.md |
| W5 | Stile | CRLF/LF misti | 5 min | server.py, capabilities.py |
| W6 | Stile | `__all__` mancante | 1 min | __init__.py |
| W7 | Igiene | `.gitignore` lacune | 1 min | .gitignore |
| W8 | Meta | Versione 0.4.0 | 3 min | pyproject.toml, CHANGELOG |
| W9 | UX | CLI help default visibili | 3 min | server.py |

---

## Microfasi

```
MF 1 — Bugfix (W1 + W2 + W3) ~13 min
MF 2 — Documentazione (W4 + W9) ~5 min
MF 3 — Igiene (W5 + W6 + W7 + W8) ~10 min
```

**Totale**: 9 items, 3 microfasi, ~28 minuti.

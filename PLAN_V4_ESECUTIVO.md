# Piano Esecutivo V4 — MCP Manager

9 items, 3 microfasi, ~28 minuti.

---

## MF 1 — Bugfix (~13 min)

### 1.1 — `prefer_remote` nella firma di gen_config (W1)

**File**: `src/mcp_manager/server.py:292`

**Task**: Aggiungere `prefer_remote: bool = False` alla firma della funzione.

**Verifica**:
```bash
python -c "
import asyncio
from mcp_manager.server import server
async def main():
    tools = await server.list_tools()
    gen = next(t for t in tools if t.name == 'generate_mcp_config')
    has = 'prefer_remote' in gen.inputSchema.get('properties', {})
    print('OK' if has else 'FAIL')
asyncio.run(main())
"
```

---

### 1.2 — `prog` in ArgumentParser (W2)

**File**: `src/mcp_manager/server.py:560`

**Task**: Aggiungere `prog="mcp-manager"` ad `ArgumentParser(...)`.

**Verifica**:
```bash
python -m mcp_manager --help | head -1
# Output: usage: mcp-manager [-h] ...
```

---

### 1.3 — Fix `--http` o renderlo documentato (W3)

**File**: `src/mcp_manager/server.py:578`

**Task**: FastMCP.run() usa SSE su `/sse` e messaggi su `/messages/`. Per far funzionare `server.run(host, port)`, bisogna verificare che FastMCP supporti `host` e `port`. Se non funziona, documentare che `--http` richiede un setup aggiuntivo.

**Fix**: (Opzione A) Provare con UVICORN dietro. (Opzione B) Usare `server.run(host=args.host, port=args.port, transport="sse")` se supportato. (Opzione C) Se non possibile, modificare help dicendo che --http e' in sviluppo.

**Verifica**: `curl http://127.0.0.1:9876/sse` risponde.

---

## MF 2 — Documentazione (~5 min)

### 2.1 — `GITHUB_CACHE_TTL` in README (W4)

**File**: `README.md`

**Task**: Aggiungere riga alla tabella env var.

**Verifica**: `grep GITHUB_CACHE_TTL README.md` restituisce riga.

---

### 2.2 — Default visibili in `--help` (W9)

**File**: `src/mcp_manager/server.py`

**Task**: Modificare help delle opzioni `--port` e `--host` per mostrare i default.

**Verifica**:
```bash
python -m mcp_manager --help
# --port PORT  HTTP port (default: 8000)
# --host HOST  HTTP host (default: 127.0.0.1)
```

---

## MF 3 — Igiene (~10 min)

### 3.1 — CRLF -> LF (W5)

**File**: `src/mcp_manager/server.py`, `src/mcp_manager/utils/capabilities.py`

**Task**: Convertire line endings da CRLF a LF.

**Verifica**: `grep -rl $'\r' src/ | head` non mostra server.py.

---

### 3.2 — `__all__` in `__init__.py` (W6)

**File**: `src/mcp_manager/__init__.py`

**Task**: Aggiungere `__all__ = ["__version__"]`.

**Verifica**:
```bash
python -c "from mcp_manager import *; print(__version__)"
```

---

### 3.3 — `.gitignore` pyc lacune (W7)

**File**: `.gitignore`

**Task**: Aggiungere `scripts/__pycache__/` e `tests/__pycache__/`.

**Verifica**: `cat .gitignore | grep scripts`

---

### 3.4 — Bump a 0.4.0 (W8)

**File**: `pyproject.toml`, `src/mcp_manager/__init__.py`, `CHANGELOG.md`

**Task**: Incrementare versione e aggiungere CHANGELOG.

**Verifica**: `python -m mcp_manager --version` restituisce `mcp-manager v0.4.0`.

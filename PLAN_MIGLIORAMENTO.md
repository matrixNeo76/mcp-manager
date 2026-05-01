# Piano di Miglioramento — MCP Manager

Analisi approfondita del codice (10 tool, 4 moduli utility, ~1800 linee) con test su edge case reali.

---

## 🔴 BUG — Priorità Alta

### B1. `MCP_CONFIG_PATH` verso file inesistente non solleva errore

**File**: `src/mcp_manager/utils/config.py:18-22`

**Problema**: Se `MCP_CONFIG_PATH` punta a un file che non esiste, `find_mcp_config()` ignora silenziosamente la variabile e cerca da CWD invece di avvertire l'utente.

**Fix**: Se `MCP_CONFIG_PATH` è impostata ma il file non esiste, sollevare `FileNotFoundError` con messaggio chiaro:
```
MCP_CONFIG_PATH=/path/to/nonexistent/.mcp.json — file not found
```

---

### B2. `code-search-mcp` falsamente marcato come ridondante

**File**: `src/mcp_manager/utils/capabilities.py`

**Problema**: La keyword "search" in `search_web` fa sì che server come `code-search-mcp` (semantic code search) vengano marcati ridondanti. Pi non ha semantic code search.

**Fix**: Aggiungere eccezioni specifiche alla categoria `search_web`: se il nome contiene "code search" o "semantic search", skip del match. Oppure rendere i keyword match più specifici ("web search" invece di solo "search").

---

### B3. `compute_composite_score(0, 0, 0)` restituisce 30.0

**File**: `src/mcp_manager/utils/capabilities.py:165-174`

**Problema**: Quando trust_score=0 e value_score=0, `non_redundancy = 100 - 0 = 100`, quindi composite = 0×0.40 + 100×0.30 + 0×0.30 = 30. Questo è fuorviante — un server senza stelle e senza valore non dovrebbe avere score 30.

**Fix**: Aggiungere un minimo: se trust_score + value_score == 0, composite = 0. Oppure normalizzare la formula.

---

## 🟡 EDGE CASES — Priorità Media

### E1. `generate_mcp_config` supporta solo npm e pypi

**File**: `src/mcp_manager/server.py:220-230`

**Problema**: I package registry `oci` (container), `nuget` (.NET), e `mcpb` (MCP bundle) non sono gestiti. Il codice casca su `else: { command: "npx", args: ["-y", identifier] }` che non funziona per questi tipi.

**Fix**: Aggiungere branch per:
- `oci` → `docker run ...`
- `nuget` → `dotnet tool run ...`
- `mcpb` → download diretto + esecuzione

---

### E2. `get_server_detail` con caratteri speciali nell'URL

**File**: `src/mcp_manager/utils/registry.py:80-90`

**Problema**: Nomi server con caratteri speciali (`@`, `#`, spazi) causano errori di URL encoding silenziosi.

**Fix**: Validare il nome server prima di inviare la richiesta. Se contiene caratteri non validi, restituire errore descrittivo invece di 404.

---

### E3. Multi-categoria non supportata in `classify_value`

**File**: `src/mcp_manager/utils/capabilities.py:135-160`

**Problema**: `classify_value` restituisce UNA sola categoria (la prima che matcha ≥3 keywords). Un server che fa sia database che monitoring (es. `db-monitor`) viene classificato solo come database.

**Fix**: Supportare multi-label: restituire un array `value_types[]` con tutte le categorie che matchano, ordinate per confidence.

---

### E4. `audit_workspace_mcp` cerca solo 3 risultati dal registry

**File**: `src/mcp_manager/server.py:290`

**Problema**: `registry_list(search=name, limit=3, version="latest")` può perdere il match se il nome locale è molto diverso dal nome registry.

**Fix**: Aumentare limit a 10 o usare ricerca più flessibile (substring + fuzzy).

---

### E5. Nessun warning quando si è senza `GITHUB_TOKEN`

**File**: `src/mcp_manager/utils/github.py:20`

**Problema**: Senza `GITHUB_TOKEN`, il rate limit è 60 req/h — esauribile in una singola query `search_with_trust` con 20+ risultati. L'utente non viene avvisato.

**Fix**: Aggiungere warning nel response quando si avvicina il rate limit, suggerendo di settare `GITHUB_TOKEN`.

---

## 🟢 MIGLIORIE — Priorità Bassa

### M1. Forzare refresh cache GitHub

**File**: `src/mcp_manager/utils/github.py`

**Problema**: Cache in-memory con TTL 5 minuti, ma nessun modo per forzare il refresh. Se un utente vuole rivalutare un server, riceve dati vecchi.

**Fix**: Aggiungere parametro `force_refresh` opzionale a `fetch_repo_info()` e ai tool che la chiamano.

---

### M2. Aggiungere categoria "Analytics / BI" a VALUE_CLASSIFICATION

**File**: `src/mcp_manager/utils/capabilities.py`

**Problema**: Server come `analytics-dashboard`, `bi-tools`, `reporting` non hanno categoria — finiscono come `uncategorized` con score 30.

**Fix**: Aggiungere nuova categoria:
```python
{
    "value_type": "analytics",
    "value_score": 75,
    "label": "Analytics / BI",
    "keywords": ["analytics", "dashboard", "reporting", "bi", "chart", "kpi"],
}
```

---

### M3. Aggiungere categoria "AI / ML" a VALUE_CLASSIFICATION

**Problema**: Server AI/ML (inference, embedding, LLM-serving) non hanno categoria dedicata.

**Fix**: Aggiungere:
```python
{
    "value_type": "ai_ml",
    "value_score": 85,
    "label": "AI / ML",
    "keywords": ["inference", "embedding", "llm", "model serving", "ml pipeline"],
}
```

---

### M4. `generate_mcp_config` non include le environment variables dai packages

**File**: `src/mcp_manager/server.py`

**Problema**: Il Registry fornisce `environmentVariables` nei package metadata, ma `generate_mcp_config` non li propaga nel config generato. L'utente deve aggiungerli manualmente.

**Fix**: Estrarre `environmentVariables` dal package detail e generarli nel blocco `env` del config.

---

### M5. Aggiungere timeout configurabile per Registry API

**File**: `src/mcp_manager/utils/registry.py`

**Problema**: Il timeout httpx è hardcoded a 30 secondi (default). In rete lenta, le richieste con paginazione multipla possono impiegare molto.

**Fix**: Aggiungere `REGISTRY_TIMEOUT` env var o parametro opzionale.

---

### M6. Batch processing parallelo per trust evaluation

**File**: `src/mcp_manager/server.py:_enrich_with_scores`

**Problema**: La valutazione trust dei server avviene in sequenza (un GitHub API call alla volta). Con 20+ risultati, ci vuole molto tempo.

**Fix**: Usare `asyncio.gather()` per valutare trust in parallelo (massimo 5 richieste concorrenti per evitare rate limit).

---

## 📊 Tabella riassuntiva

| ID | Tipo | Cosa | Sforzo | Impatto |
|----|------|------|--------|---------|
| B1 | Bug | `MCP_CONFIG_PATH` non fallisce | 🔵 5 min | Alto |
| B2 | Bug | `code-search-mcp` falsa ridondanza | 🔵 5 min | Alto |
| B3 | Bug | `composite_score(0,0,0)` = 30 | 🔵 5 min | Medio |
| E1 | Edge | Solo npm/pypi in config gen | 🟡 15 min | Medio |
| E2 | Edge | Caratteri speciali in URL | 🔵 5 min | Basso |
| E3 | Edge | Multi-categoria non supportata | 🟡 20 min | Medio |
| E4 | Edge | Audit cerca solo 3 risultati | 🔵 5 min | Basso |
| E5 | Edge | Nessun warning rate limit | 🔵 10 min | Medio |
| M1 | Miglioria | Force refresh cache | 🔵 5 min | Basso |
| M2 | Miglioria | Categoria Analytics/BI | 🔵 5 min | Basso |
| M3 | Miglioria | Categoria AI/ML | 🔵 5 min | Basso |
| M4 | Miglioria | Env vars nei package | 🟡 15 min | Medio |
| M5 | Miglioria | Timeout configurabile | 🔵 5 min | Basso |
| M6 | Miglioria | Batch parallelo trust | 🟡 20 min | Medio |

## 🚀 Ordine di implementazione consigliato

```
Sprint 1 (bugfix):
  B1 → B2 → B3 → E5

Sprint 2 (edge cases):
  E1 → E3 → E4 → E2

Sprint 3 (migliorie):
  M6 → M4 → M2 → M3 → M1 → M5
```

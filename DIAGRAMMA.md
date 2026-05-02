# MCP Manager — Diagramma Architetturale

## 1. Visione d'Insieme

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LLM / AI Agent                               │
│              (Claude, Copilot, Cursor, Gemini...)                    │
│                                                                      │
│  Chiama strumenti MCP per:                                          │
│  - Cercare server sul registry                                       │
│  - Valutare trust di un repository                                    │
│  - Generare configurazioni                                            │
│  - Auditare il workspace                                              │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       mcp-manager (FastMCP)                          │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                     server.py (84 righe)                        │  │
│  │  - Crea istanza FastMCP                                         │  │
│  │  - Registra 6 moduli tool                                       │  │
│  │  - CLI: --version, --http, --port, --host                       │  │
│  └────────────────────────┬───────────────────────────────────────┘  │
│                           │                                          │
│           ┌───────────────┼──────────────────────────┐               │
│           ▼               ▼                          ▼               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────────┐  │
│  │ tools/        │ │ utils/       │ │ data/                        │  │
│  │ (6 moduli)    │ │ (4 moduli)   │ │ capabilities.json            │  │
│  │ 11 strumenti  │ │ Logica core  │ │ (12 categorie pi built-in)   │  │
│  └──────────────┘ └──────────────┘ └──────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────┐                   │
│  │ types.py (11 TypedDict per type safety)       │                   │
│  └──────────────────────────────────────────────┘                   │
└──────────────────────────────────────────────────────────────────────┘
           │                    │                      │
           ▼                    ▼                      ▼
   ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
   │ .mcp.json     │    │ MCP Registry │    │   GitHub API     │
   │ (locale)      │    │ registry.    │    │   api.github.com │
   │ lettura/      │    │ modelcontext │    │                  │
   │ scrittura     │    │ protocol.io  │    │ stars, forks,    │
   │               │    │              │    │ ultimo aggiorn.  │
   └──────────────┘    └──────────────┘    └──────────────────┘
```

---

## 2. Struttura dei Moduli (1796 righe)

### 2.1 Tools (6 moduli, 11 strumenti)

```
┌──────────────────────────────────────────────────────────────────────┐
│                     tools/ (6 file, 539 righe)                      │
├──────────────────────┬───────────────────────────────────────────────┤
│ local_tools.py (15)  │ list_local_servers — Legge .mcp.json locale   │
├──────────────────────┼───────────────────────────────────────────────┤
│ trust_tools.py (41)  │ assess_trustworthiness — Trust score GitHub   │
├──────────────────────┼───────────────────────────────────────────────┤
│ info_tools.py (27)   │ get_server_details — Dettaglio server         │
│                      │ registry_health — Health check registry       │
├──────────────────────┼───────────────────────────────────────────────┤
│ config_tools.py(108) │ generate_mcp_config — Genera .mcp.json entry  │
│                      │   (npm/pypi/oci/nuget/mcpb)                   │
├──────────────────────┼───────────────────────────────────────────────┤
│ search_tools.py(178) │ search_registry — Cerca sul registry          │
│                      │ search_with_trust — Ricerca + trust score     │
│                      │ search_useful_mcp — Ricerca smart (filtra     │
│                      │   server ridondanti)                          │
│                      │ _enrich_with_scores — Arricchisce risultati   │
│                      │   con trust + ridondanza + valore + composito │
├──────────────────────┼───────────────────────────────────────────────┤
│ audit_tools.py(170)  │ audit_workspace_mcp — Audit workspace         │
│                      │ compare_alternatives — Confronta alternative   │
│                      │ pi_capabilities — Mostra built-in di pi       │
└──────────────────────┴───────────────────────────────────────────────┘
```

### 2.2 Utils (4 moduli)

```
┌──────────────────────────────────────────────────────────────────────┐
│                     utils/ (4 file, 1022 righe)                     │
├──────────────────────┬───────────────────────────────────────────────┤
│ config.py (119)      │ Lettura/scrittura .mcp.json                   │
│                      │ Ricerca automatica dal CWD o MCP_CONFIG_PATH │
│                      │ Dry-run per scritture sicure                  │
├──────────────────────┼───────────────────────────────────────────────┤
│ github.py (282)      │ Client GitHub API + trust score               │
│                      │ Cache in-memory (GITHUB_CACHE_TTL, def 300s)  │
│                      │ RateLimitTracker thread-safe                  │
│                      │ Trust score:                                   │
│                      │   70% stelle + 20% recency + 10% forks        │
├──────────────────────┼───────────────────────────────────────────────┤
│ registry.py (243)    │ Client MCP Registry API                       │
│                      │ Cache (REGISTRY_CACHE_TTL, default 60s)       │
│                      │ Paginazione automatica con cursore             │
│                      │ Version-aware (REGISTRY_API_VERSION)           │
├──────────────────────┼───────────────────────────────────────────────┤
│ capabilities.py(378) │ Rilevamento ridondanza vs pi built-in          │
│                      │ Classificazione valore d'uso (12 categorie)    │
│                      │ Score composito:                               │
│                      │   trust x 0.40 + (100-red) x 0.30 + val x 0.30│
└──────────────────────┴───────────────────────────────────────────────┘
```

---

## 3. Scoring Composito

```
┌──────────────────────────────────────────────────────────────────────┐
│                  SCORE COMPOSITO per ogni server                     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  composite = trust_score x 0.40   ◄── Stelle GitHub, recency, forks │
│            + (100 - redundancy) x 0.30  ◄── pi ha gia' questo tool? │
│            + value_score x 0.30    ◄── Database? Cloud? API?         │
│                                                                      │
│  trust_score = stars_score + recency_score + forks_score (0-100)     │
│    stars_score   = min(stars / min_stars, 1.0) x 70                  │
│    recency_score = aggiornato <90gg ? 20 : decade linearmente        │
│    forks_score   = min(forks / 10, 1.0) x 10                         │
│    is_trusted    = trust_score >= 50                                  │
│                                                                      │
│  redundancy_score = 0-100 (0 = unico, 100 = completamente ridondante)│
│    Basato su: name patterns (+40), keywords (+15), esempi noti (+100)│
│    Penalita': se e' API wrapper (-20), se e' cloud/infra (-40)       │
│                                                                      │
│  value_score = 0-100 (30 = generico, 90 = database)                  │
│    Categorie: Database(90), Cloud/DevOps(85), Payments(85),          │
│    AI/ML(85), Project Mgmt(80), Communication(80), Monitoring(80),   │
│    Design(75), Analytics/BI(75), Media(75), Geolocation(70),         │
│    E-commerce/CMS(70), [RED] Ridondante(5-30)                        │
│                                                                      │
│  Se trust_score=0 E value_score=0 → composite=0 (non 30)             │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Flusso `search_useful_mcp`

```
search_useful_mcp(query="database")
         │
         ▼
┌─────────────────────────────┐
│ 1. registry_list("database") │  ◄── Chiamata API Registry
│    limit=20, version=latest  │       Cache: 60s TTL
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 2. compute_redundancy()      │  ◄── Match contro pi built-in
│    per ogni risultato         │       (filesystem, browser, shell...)
│    → redundancy_score (0-100) │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 3. classify_value()          │  ◄── Match contro categorie valore
│    per ogni risultato         │       (database, cloud, ai_ml...)
│    → value_score, value_type  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 4. fetch_repo_info()         │  ◄── GitHub API (parallelo, max 5)
│    per ogni risultato         │       Cache: 300s TTL
│    → stars, forks, days       │       Thread-safe RateLimitTracker
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 5. compute_composite_score() │  ◄── trust x 0.40
│    trust + redundancy + value │       non-red x 0.30
│    → composite_score (0-100)  │       value x 0.30
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 6. Filtra ridondanti         │  ◄── Se include_redundant=False
│    (redundant=True → rimossi) │       (default: True)
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 7. Ordina per composite      │  ◄── Dal piu' utile al meno
│    Score decrescente          │
└─────────────┬───────────────┘
              │
              ▼
       Risultati arricchiti
       (11 campi per server)
```

---

## 5. Architettura Dati

```
┌──────────────────────────────────────────────────────────────────────┐
│                      TIPI (types.py)                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ServerEntry     ◄── Risultato base dal Registry (name, version...)  │
│       │                                                              │
│       ▼                                                              │
│  EnrichedServer  ◄── Arricchito con trust + ridondanza + valore     │
│  (ServerEntry + stars, trust_score, redundancy_score, value_score,  │
│   composite_score, is_trusted, value_type, value_label...)           │
│                                                                      │
│  TrustScore      stars_score + recency_score + forks_score + warnings│
│  RedundancyResult  redundancy_score + redundant + category + reason  │
│  ValueResult     value_type + value_score + value_label + tipi[]     │
│                                                                      │
│  LocalServer     ◄── Server in .mcp.json (name, command, args...)    │
│  AuditEntry      ◄── Entry nell'audit (local_name, trust, conflitti)│
│  ServerDetail    ◄── Dettaglio completo dal Registry                 │
│                                                                      │
│  RateLimitStatus ◄── Stato rate limit GitHub (remaining, reset...)   │
│  RegistryHealth  ◄── Health check del Registry (reachable, count...) │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                      DATI STATICI                                     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  data/capabilities.json (v2)                                          │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ 12 categorie built-in di pi:                                    │  │
│  │ - Filesystem (read, write, edit, grep, find, ls)                │  │
│  │ - Browser Automation (browser_tool)                              │  │
│  │ - Shell (bash, script_sandbox)                                   │  │
│  │ - Web Search & Fetch (web_search, web_fetch)                     │  │
│  │ - AI/LLM (call_llm, spawn_session)                               │  │
│  │ - Memory & Persistence (remember, search_memory...)               │  │
│  │ - Code Analysis (grep, find)                                     │  │
│  │ - Skills & MCP Management (skillsmp, mcp-manager)                │  │
│  │ - Session Orchestration (spawn_session, send_agent_message...)    │  │
│  │ - Messaging (Telegram, WhatsApp)                                  │  │
│  │ - Data Transform (transform_data)                                 │  │
│  │ - Templating & Render (render_template)                           │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 6. Configurazione e Variabili d'Ambiente

```
┌──────────────────────────────────────────────────────────────────────┐
│                    ENVIRONMENT VARIABLES                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  GITHUB_TOKEN          (obbligatorio per >60 req/h)                  │
│  GITHUB_TIMEOUT        Default: 15s                                  │
│  GITHUB_CACHE_TTL      Default: 300s (5 min)                        │
│  REGISTRY_TIMEOUT      Default: 30s                                  │
│  REGISTRY_CACHE_TTL    Default: 60s                                  │
│  REGISTRY_API_VERSION  Default: "v0.1"                               │
│  MCP_CONFIG_PATH       Override percorso .mcp.json                    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                  .mcp.json (configurazione utente)                    │
├──────────────────────────────────────────────────────────────────────┤
│  {                                                                   │
│    "mcpServers": {                                                   │
│      "mcp-manager": {                                                │
│        "command": "python",                                          │
│        "args": ["-m", "mcp_manager"],                                │
│        "cwd": "C:/Users/auresystem/mcp-manager"                      │
│      }                                                               │
│    }                                                                 │
│  }                                                                   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 7. Test (70 test, 5 file)

```
┌──────────────────────────────────────────────────────────────────────┐
│                          TEST                                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  tests/                                                              │
│  ├── test_capabilities.py  (25)  ◄── Ridondanza, valore, composito  │
│  ├── test_github.py        (18)  ◄── URL parsing, trust score, mock  │
│  ├── test_config.py        (13)  ◄── Lettura/scrittura .mcp.json     │
│  ├── test_registry.py      (8)   ◄── Registry API, mock integration  │
│  ├── test_server.py        (6)   ◄── Tool registration, parametri    │
│  └── test_cli.py           (nuovo) ◄── Argparse, version, help       │
│                                                                      │
│  scripts/                                                            │
│  └── smoke_test.py         (7 test)  ◄── End-to-end su API reali     │
│                                                                      │
│  .github/                                                            │
│  └── workflows/test.yml    ◄── CI: Python 3.12 + 3.13 matrix        │
│                                                                      │
│  Esecuzione:                                                         │
│    uv run python -m pytest tests/ -v   # 70 test                     │
│    uv run python scripts/smoke_test.py  # 7 test end-to-end          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 8. Commit History (14 commit su main)

```
cd6b0b6 ── feat: initial MCP Manager (9 tools)
   │
02bd7ce ── feat: pi capability awareness + redundancy filtering
   │
516d70f ── docs: comprehensive repo documentation
   │
de1188d ── fix: 3 bugs, 5 edge cases, 6 improvements
   │
5672b81 ── fix: Sprint 1-3 (62 tests, 11 tools, 0 emoji)
   │
71a2772 ── docs: update for v0.3.0
   │
f4823ac ── fix: V4 (CLI, CI, rate limit reset, 70 tests)
   │
62a9d20 ── docs: v0.4.0 README, AGENTS, CLAUDE
   │
51a12ff ── refactor: V5 architecture (tools/, types.py, thread safety)
   │
b229b32 ── chore: remove old plan files
   │
f3ab2cf ── fix: V4 completed (prefer_remote, .gitattributes, __all__)
   │
  ...    ── (3 commit minori)
```

---

## 9. Metriche

```
┌──────────────────────────────────────────────────────────────────────┐
│                         METRICHE                                     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Linee di codice:    1.796  (senza test)                             │
│  File sorgente:      14     (.py + .json)                            │
│  Tool MCP:           11                                              │
│  Moduli tool:        6     (1 ogni ~90 righe)                       │
│  Moduli utils:       4                                               │
│  TypedDict:          11    (types.py)                                │
│  Test:               70    (5 file)                                  │
│  Commit:             14    (su main)                                 │
│  Versione:           0.4.0                                           │
│  Licenza:            MIT                                             │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

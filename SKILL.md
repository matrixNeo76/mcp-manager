---
name: mcp-manager
description: MCP server per scoprire, valutare e gestire altri MCP server. Cerca sul registry ufficiale, valuta l'affidabilità via GitHub stars, confronta alternative e genera configurazioni pronte per .mcp.json.
---

# MCP Manager

Questo MCP server ti permette di **gestire l'intero ecosistema dei tuoi MCP server**:
- **Scoprire** nuovi MCP server dal registry ufficiale
- **Valutare** l'affidabilità di ogni server (GitHub stars, recency, forks)
- **Filtrare** server ridondanti (che duplicano capacità già in pi/Craft Agents)
- **Confrontare** alternative per lo stesso use case
- **Generare** configurazioni pronte per `.mcp.json`
- **Auditare** la configurazione attuale

## Tool disponibili (11)

| Tool | Cosa fa |
|------|---------|
| `list_local_servers` | Elenca i server MCP configurati nel `.mcp.json` locale |
| `search_registry` | Cerca server sul registry ufficiale `registry.modelcontextprotocol.io` |
| `get_server_details` | Ottiene info dettagliate di un server (packages, repository, transports) |
| `assess_trustworthiness` | Valuta l'affidabilità di un repository GitHub (stelle, aggiornamenti, forks) |
| `search_with_trust` | Cerca + valuta trust + ridondanza + valore, ranking composito |
| `search_useful_mcp` | 🔥 Come search_with_trust ma **filtra i server ridondanti** automaticamente |
| `compare_alternatives` | Confronta più server per lo stesso use case con score composito |
| `generate_mcp_config` | Genera un blocco di configurazione pronto per `.mcp.json` |
| `audit_workspace_mcp` | Audit completo con **rilevamento ridondanza** e raccomandazioni |
| `registry_health` | Verifica lo stato di salute del registry |
| `pi_capabilities` | Mostra le capacità built-in di pi per capire cosa è ridondante |

## Score composito

Ogni server valutato con `search_useful_mcp` o `search_with_trust` riceve:

```
composite_score = trust_score x 0.40   # Stelle GitHub, recency, forks
                + (100 - redundancy) x 0.30  # pi gia lo ha?
                + value_score x 0.30    # Database? Cloud? API?
```

### Trust score (0-100)
- **70%** — Stelle GitHub (rispetto a `min_stars`)
- **20%** — Recency (aggiornato negli ultimi 90 giorni)
- **10%** — Fork
- `is_trusted = True` se trust_score >= 50

### Ridondanza
- **redundancy_score** (0-100): quanto duplica capacità già in pi
- **redundant** (bool): True se score >= 50
- Rileva: filesystem, browser, shell, search web, memoria, code analysis...

### Valore d'uso
- **value_type**: categoria (database, cloud_devops, project_management, monitoring...)
- **value_score**: 0-100 quanto valore aggiunge come integrazione esterna
- **value_types[]**: multi-categoria (es. database + monitoring)

## Esempi d'uso

### Cercare server UTILI (non ridondanti)
```
search_useful_mcp(query="database", limit=10, filter_untrusted=True)
```

### Cercare server con valutazione completa
```
search_with_trust(query="notion", limit=10)
```

### Confrontare alternative
```
compare_alternatives(query="search", limit=5)
```

### Generare configurazione per installazione
```
generate_mcp_config(
  server_name="io.github.user/awesome-server",
  server_label="awesome",
  dry_run=True  # False per scrivere su .mcp.json
)
```

### Audit completo con rilevamento ridondanza
```
audit_workspace_mcp()
```

### Verificare capacità pi
```
pi_capabilities()
```

## Filtri avanzati

| Parametro | Default | Effetto |
|-----------|---------|---------|
| `filter_untrusted` | `true` in search_useful_mcp | Mostra solo server con trust >= 50 |
| `include_redundant` | `false` in search_useful_mcp | Include anche server che duplicano pi |
| `min_stars` | 10 | Stelle GitHub minime raccomandate |

---
name: mcp-manager
description: MCP server per scoprire, valutare e gestire altri MCP server. Cerca sul registry ufficiale, valuta l'affidabilità via GitHub stars, confronta alternative e genera configurazioni pronte per .mcp.json.
---

# MCP Manager

Questo MCP server ti permette di **gestire l'intero ecosistema dei tuoi MCP server**:
- **Scoprire** nuovi MCP server dal registry ufficiale
- **Valutare** l'affidabilità di ogni server (GitHub stars, recency, forks)
- **Confrontare** alternative per lo stesso use case
- **Generare** configurazioni pronte per `.mcp.json`
- **Auditare** la configurazione attuale

## Tool disponibili

| Tool | Cosa fa |
|------|---------|
| `list_local_servers` | Elenca i server MCP configurati nel `.mcp.json` locale |
| `search_registry` | Cerca server sul registry ufficiale `registry.modelcontextprotocol.io` |
| `get_server_details` | Ottiene info dettagliate di un server (packages, repository, transports) |
| `assess_trustworthiness` | Valuta l'affidabilità di un repository GitHub (stelle, aggiornamenti, forks) |
| `search_with_trust` | Cerca + valuta trust, ordina per trust score (dal più affidabile) |
| `compare_alternatives` | Confronta più server per lo stesso use case con trust score |
| `generate_mcp_config` | Genera un blocco di configurazione pronto per `.mcp.json` |
| `audit_workspace_mcp` | Audit completo della configurazione MCP locale |
| `registry_health` | Verifica lo stato di salute del registry |

## Esempi d'uso

### Cercare server per un task
```
search_registry(query="postgres", limit=10)
```

### Trovare il server più affidabile
```
search_with_trust(query="filesystem", min_stars=20, filter_untrusted=True)
```

### Confrontare alternative
```
compare_alternatives(query="brave search", limit=5)
```

### Generare configurazione per installazione
```
generate_mcp_config(
  server_name="io.github.user/awesome-server",
  server_label="awesome",
  dry_run=True  # False per scrivere su .mcp.json
)
```

### Audit completo
```
audit_workspace_mcp()
```

## Trust score

Il trust score (0-100) si basa su:
- **70%** — Stelle GitHub (rispetto a `min_stars`)
- **20%** — Recency (aggiornato negli ultimi 90 giorni)
- **10%** — Fork

`is_trusted = True` se trust_score >= 50.

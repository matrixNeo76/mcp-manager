# Piano Integrazione Database MCP per Craft Agents OSS

Ricerca eseguita con mcp-manager su 10 candidati, selezionati i migliori 4.

---

## 🏆 Risultati Ricerca

### SQLite — Migliori server

| # | Server | ⭐ Stelle | Trust | Composite | Package |
|---|--------|:--------:|:-----:|:---------:|---------|
| 1 | **neverinfamous/sqlite-mcp-server** v2.6.3 | 13 | 94/100 | 91.6 | `sqlite-mcp-server-enhanced` (pypi) |
| 2 | **ofershap/sqlite** v1.0.1 | 1 | 90/100 | 90.0 | `mcp-sqlite-server` (npm) |

### PostgreSQL — Migliori server

| # | Server | ⭐ Stelle | Trust | Composite | Trasporto |
|---|--------|:--------:|:-----:|:---------:|-----------|
| 1 | **waystation/postgres** v0.3.1 | 50 | 89/100 | 92.7 | Remote HTTP (streamable-http) |
| 2 | **hovecapital/read-only-postgres** v0.1.0 | 2 | 91/100 | 93.3 | npm stdio |

---

## 🥇 Raccomandazione

### SQLite: `neverinfamous/sqlite-mcp-server` (vincitore)

**Perche':**
- 73 tool: JSONB, full-text search, geospatial, analytics
- Pypi package → installazione con `uv pip install`
- 13 stelle, trust 94/100
- Attivamente mantenuto

### PostgreSQL: `ai.waystation/postgres` (vincitore)

**Perche':**
- 50 stelle (il piu' popolare)
- Remote HTTP → nessuna installazione locale
- Trust 89/100
- Connessione diretta a database PostgreSQL

---

## ⚙️ Configurazione per `.mcp.json`

### SQLite (via pypi/stdin)

```json
{
  "mcpServers": {
    "sqlite": {
      "command": "python",
      "args": ["-m", "sqlite_mcp_server_enhanced"],
      "cwd": "C:/Users/auresystem/mcp-manager"
    }
  }
}
```

**Installazione:**
```bash
uv pip install sqlite-mcp-server-enhanced
```

### PostgreSQL (via Remote HTTP)

```json
{
  "mcpServers": {
    "postgres": {
      "url": "https://waystation.ai/postgres/mcp",
      "type": "streamable-http"
    }
  }
}
```

**Configurazione:** Il server remoto richiede credenziali Waystation (servizio hosted).

### Alternativa PostgreSQL (via npm/stdin)

```json
{
  "mcpServers": {
    "postgres-local": {
      "command": "npx",
      "args": ["-y", "@hovecapital/read-only-postgres-mcp-server"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/db"
      }
    }
  }
}
```

---

## 📋 Azioni Consigliate

| # | Azione | Priorità |
|---|--------|----------|
| 1 | Testare `neverinfamous/sqlite-mcp-server` in isolamento | Alta |
| 2 | Valutare se SQLite via MCP serve o basta il tool `transform_data` di pi | Media |
| 3 | Per PostgreSQL, testare waystation (remote) vs hovecapital (locale) | Alta |
| 4 | Decidere se integrare permanentemente o usare on-demand | Media |

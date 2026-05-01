# MCP Manager 🔧

> **Discover, evaluate, and manage MCP servers from the official registry — with built-in awareness of what pi/Craft Agents already provides.**

MCP Manager is an MCP server that acts as a **governance hub** for your entire MCP ecosystem. It helps you find new MCP servers, evaluate their trustworthiness, check if they add real value beyond pi's built-in capabilities, and generate ready-to-use configuration.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Registry Search** | Search the official MCP Registry (`registry.modelcontextprotocol.io`) |
| ⭐ **Trust Evaluation** | GitHub stars, recency, forks → trust score (0–100) |
| 🧠 **pi Awareness** | Knows what pi/Craft Agents already does — filters out redundant servers |
| 📊 **Value Classification** | Database, Cloud/DevOps, Project Mgmt, Monitoring, Payments, Design, etc. |
| 🔄 **Composite Scoring** | trust_score × 40% + non-redundancy × 30% + value × 30% |
| 📋 **Workspace Audit** | Full audit of your local `.mcp.json` with redundancy warnings |
| ⚙️ **Config Generator** | Generate ready-to-use `.mcp.json` entries from registry metadata |
| 🏥 **Registry Health** | Health check of the official MCP Registry |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
git clone https://github.com/matrixNeo76/mcp-manager.git
cd mcp-manager
uv sync
uv pip install -e .
```

### Run

```bash
# Direct
python -m mcp_manager.server

# Or via the CLI entry point
mcp-manager
```

### Add to your project's `.mcp.json`

```json
{
  "mcpServers": {
    "mcp-manager": {
      "command": "python",
      "args": ["-m", "mcp_manager.server"],
      "cwd": "/path/to/mcp-manager"
    }
  }
}
```

> **Tip:** Set `GITHUB_TOKEN` in your environment for 5,000 API requests/hour instead of the default 60.

---

## 🛠️ Tools

| Tool | Description |
|------|-------------|
| `list_local_servers` | List MCP servers configured in your `.mcp.json` |
| `search_registry(query, limit)` | Search the official MCP Registry |
| `get_server_details(name)` | Detailed info: packages, repository, transports |
| `assess_trustworthiness(url, min_stars)` | GitHub trust score (stars, recency, forks) |
| `search_with_trust(query, limit)` | Registry search + trust + redundancy + value scoring |
| **`search_useful_mcp(query, limit)`** | 🔥 **Smart search** — filters redundant servers automatically |
| `compare_alternatives(query)` | Compare servers side-by-side for a task |
| `generate_mcp_config(name)` | Generate `.mcp.json` block (dry-run by default) |
| `audit_workspace_mcp()` | Full audit with redundancy detection and recommendations |
| `registry_health()` | Check if the MCP Registry is reachable |

---

## 📊 Smart Scoring

When you use `search_useful_mcp` or `search_with_trust`, every result includes:

```
composite_score = trust_score × 0.40    # GitHub stars, recency, forks
                + (100 - redundancy) × 0.30  # pi already has this?
                + value_score × 0.30     # Database? Cloud? Integration?
```

### Value Categories

| Category | Score | Examples |
|----------|-------|----------|
| 🗄️ Database | 90 | PostgreSQL, MySQL, Redis, SQLite |
| ☁️ Cloud/DevOps | 85 | Kubernetes, Docker, Cloudflare, AWS |
| 💰 Payments | 85 | Stripe, PayPal |
| 📋 Project Mgmt | 80 | Jira, Linear, Notion, Asana |
| 💬 Communication | 80 | Slack, Discord, Gmail |
| 📊 Monitoring | 80 | Sentry, Datadog, Grafana |
| 🎨 Design | 75 | Figma, Canva |
| 🔴 Redundant | 5–30 | Filesystem, Browser, Search (pi has these) |

---

## 🧪 Testing

```bash
# List all registered tools
python -c "
import asyncio
from mcp_manager.server import server
async def main():
    tools = await server.list_tools()
    for t in sorted(tools, key=lambda x: x.name):
        print(f'✅ {t.name}')
asyncio.run(main())
"

# Test registry health
python -c "
import asyncio
from mcp_manager.server import server
async def main():
    _, data = await server.call_tool('registry_health', {})
    print(data)
asyncio.run(main())
"
```

---

## 🏗️ Architecture

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full design overview.

```
mcp-manager/
├── src/mcp_manager/        # Server code
│   ├── server.py           # FastMCP server with 10 tools
│   ├── data/               # Static data
│   │   └── capabilities.json  # pi built-in capability map
│   └── utils/              # Core modules
│       ├── config.py       # .mcp.json reader/writer
│       ├── github.py       # GitHub API + trust scoring
│       ├── registry.py     # MCP Registry API client
│       └── capabilities.py # Redundancy + value scoring
├── SKILL.md                # Skill documentation
└── pyproject.toml           # Project config
```

---

## 🔐 Security

- **Read-first**: all tools are read-only by default
- **Write requires explicit flag**: `generate_mcp_config(dry_run=False)`
- **No subprocess execution**: all HTTP via `httpx`
- **No credential exposure**: GitHub token read from env var `GITHUB_TOKEN`

---

## 📄 License

MIT — see [`LICENSE`](./LICENSE).

---

## 🤝 Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for guidelines.

---

## 📦 Repository

**[matrixNeo76/mcp-manager](https://github.com/matrixNeo76/mcp-manager)** on GitHub.

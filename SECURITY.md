# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.4.x   | ✅ Active |
| < 0.4   | ❌ No longer supported |

## Reporting a Vulnerability

If you discover a security vulnerability in MCP Manager, please report it privately.

**Do not** open a public issue. Instead:

1. **GitHub Private Reporting**: Use the [Report a Vulnerability](https://github.com/matrixNeo76/mcp-manager/security/advisories/new) feature (enabled for this repository)
2. **Email**: If GitHub reporting is unavailable, email the maintainer directly

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if known)

We will acknowledge receipt within 48 hours and provide a timeline for a fix within 7 days.

## Scope

- MCP Manager source code (`src/mcp_manager/`)
- Dependencies listed in `pyproject.toml` and `uv.lock`
- CI/CD configuration (`.github/workflows/`)

## Out of Scope

- Vulnerabilities in pi/Craft Agents core platform
- Vulnerabilities in third-party MCP servers discovered via this tool
- Theoretical attacks requiring local access to the user's machine

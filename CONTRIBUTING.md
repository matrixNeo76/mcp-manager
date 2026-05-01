# Contributing to MCP Manager

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

Please be respectful and constructive. We aim to maintain a welcoming community.

## How to Contribute

### Reporting Issues

1. Check if the issue already exists in the [issue tracker](https://github.com/matrixNeo76/mcp-manager/issues)
2. Provide a clear title and description
3. Include steps to reproduce for bugs
4. Specify your environment (Python version, OS)

### Suggesting Enhancements

1. Open an issue with the "enhancement" label
2. Describe the feature and its use case
3. Explain why it adds value beyond pi's built-in capabilities

### Pull Requests

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feat/your-feature`
3. **Make your changes** following the code style
4. **Test** your changes:
   ```bash
   cd mcp-manager
   uv run python -c "
   import asyncio
   from mcp_manager.server import server
   async def main():
       tools = await server.list_tools()
       print(f'{len(tools)} tools')
   asyncio.run(main())
   "
   ```
5. **Commit** using [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` — new feature
   - `fix:` — bug fix
   - `docs:` — documentation
   - `refactor:` — code restructuring
   - `test:` — testing
   - `chore:` — maintenance
6. **Push** and open a Pull Request

## Development Setup

```bash
# Clone
git clone https://github.com/matrixNeo76/mcp-manager.git
cd mcp-manager

# Install dependencies
uv sync
uv pip install -e .

# Verify
python -m mcp_manager.server --help
```

## Coding Standards

- **Python 3.12+** — use modern typing (PEP 604, `|` for unions)
- **Type hints** — all functions must have type annotations
- **Docstrings** — all tools need clear docstrings (used as LLM-facing descriptions)
- **Error handling** — provide actionable error messages
- **No subprocess** — use `httpx` for all external communication

### Import Order

1. Standard library
2. Third-party (mcp, httpx)
3. Local (mcp_manager.*)

### Naming

- Files: `snake_case.py`
- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private helpers: `_leading_underscore`

## Testing

Run the redundancy detection tests:

```bash
uv run python -c "
from mcp_manager.utils.capabilities import compute_redundancy, classify_value
# Add test cases
tests = [
    ('io.github.example/filesystem', 'filesystem access', True),
    ('io.github.example/jira', 'Jira integration', False),
]
for name, desc, expected in tests:
    result = compute_redundancy(name, desc)
    assert result['redundant'] == expected, f'{name}: expected {expected}'
print('All tests passed')
"
```

## Adding New Capability Categories

To add a new pi built-in capability category:

1. Edit `src/mcp_manager/data/capabilities.json`
2. Add the category with keywords, name patterns, and examples
3. If it also needs a value classification, add it to `VALUE_CLASSIFICATION` in `capabilities.py`
4. Test with known redundant and non-redundant examples

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

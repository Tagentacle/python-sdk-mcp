# tagentacle-py-mcp — CI/CD & Development Instructions

## Project Overview

- **Language**: Python ≥ 3.10
- **Build**: `hatchling` (PEP 517)
- **Package**: `tagentacle_py_mcp` — MCPServerNode, TagentacleMCPServer, TACL JWT auth
- **Version**: Tracked in `pyproject.toml` — must match latest `CHANGELOG.md` release
- **Dependencies**: `tagentacle-py-core`, `mcp>=1.8`, `anyio`, `uvicorn`, `starlette`
- **Tests**: `pytest` (currently no tests — adding them is a priority)

## CI Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and PR:

### Jobs

1. **lint** — `ruff check .` + `ruff format --check .`
2. **test** — `pytest` (requires `tagentacle-py-core` as local/editable dep)
3. **build** — verify package builds cleanly

### Local Development

This package depends on `tagentacle-py-core` via path dependency (see `[tool.uv.sources]` in `pyproject.toml`). For local development:

```bash
cd /path/to/workspace
pip install -e python-sdk-core
pip install -e python-sdk-mcp
```

### Adding Tests

Create `tests/` directory at repo root:

```
tests/
├── test_server_node.py
├── test_tacl.py
├── test_transport.py
└── conftest.py
```

Example test:

```python
import pytest

@pytest.mark.asyncio
async def test_mcp_server_node_lifecycle():
    # Test that MCPServerNode can transition through lifecycle states
    ...
```

### Release Process

1. Update `CHANGELOG.md` with new version section
2. Update `version` in `pyproject.toml` to match
3. Commit: `chore: bump version to X.Y.Z`
4. Tag: `git tag vX.Y.Z`
5. Push: `git push && git push --tags`

## Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `refactor:` — code restructure
- `chore:` — tooling, CI, version bumps
- `ci:` — CI configuration changes

## Architecture Notes

- `MCPServerNode` extends `LifecycleNode` — adds Streamable HTTP MCP transport
- `TagentacleMCPServer` wraps FastMCP + bus integration (MCP tools, Daemon system service proxying)
- `/mcp/directory` topic: automatic `MCPServerDescription` publishing on activate/deactivate
- TACL (Tagentacle Access Control Layer): JWT-based auth with `PermissionMCPServerNode`
- `CallerIdentity`: extracted from JWT — `node_id`, `role`, `space`
- MCP is application layer — it runs ON the bus, not IN the bus
- This package depends on `tagentacle-py-core` but core does NOT depend on this

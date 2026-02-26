# Changelog — tagentacle-py-mcp

All notable changes to **tagentacle-py-mcp** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-26

### Added
- **MCP Transport Adapters** (library):
  - `tagentacle_client_transport(node, server_node_id)` — async context manager bridging MCP ClientSession over the bus.
  - `tagentacle_server_transport(node, server_node_id)` — async context manager exposing MCP Server as a bus service.
  - Automatic traffic mirroring to `/mcp/traffic` topic (dual-track observability).
  - Backward-compatible aliases: `TagentacleClientTransport`, `TagentacleServerTransport`.
- **TagentacleMCPServer** (executable node):
  - Built-in MCP Server exposing all bus interactions as MCP Tools.
  - Tools: `publish_to_topic`, `subscribe_topic`, `unsubscribe_topic`, `list_nodes`, `list_topics`, `list_services`, `get_node_info`, `call_bus_service`, `ping_daemon`, `describe_topic_schema`.
  - Topic allow-list support.
  - Standalone `main()` entrypoint.
- **Tagentacle pkg manifest**: `tagentacle.toml` with `type = "executable"`, entry point `tagentacle_py_mcp.server:main`.

### Changed
- **Renamed**: `MCPPublishBridge` → `TagentacleMCPServer` (breaking rename from old python-sdk).
- **Import path**: `from tagentacle_py.mcp import ...` → `from tagentacle_py_mcp import ...`.
- **Core dependency**: Depends on `tagentacle-py-core` (extracted from monolithic python-sdk).

> Extracted from the monolithic `tagentacle-py` (python-sdk) repo as part of the
> 1-repo-1-pkg architecture migration.

# Tagentacle MCP Integration

> **The ROS of AI Agents** — MCP transport layer and built-in MCP Server for the Tagentacle bus.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

`tagentacle-py-mcp` provides MCP (Model Context Protocol) integration for the Tagentacle message bus:

- **Transport Adapters** — Bridge MCP JSON-RPC sessions over the Tagentacle bus (`tagentacle_client_transport`, `tagentacle_server_transport`).
- **TagentacleMCPServer** — Built-in executable node exposing all bus interactions as MCP Tools.

## Install

```bash
pip install tagentacle-py-mcp
```

This automatically installs `tagentacle-py-core` as a dependency.

## Transport Adapters (Library)

### Client Transport (Agent → MCP Server)

```python
from tagentacle_py_core import Node
from tagentacle_py_mcp import tagentacle_client_transport
from mcp import ClientSession

node = Node("agent_node")
await node.connect()
spin_task = asyncio.create_task(node.spin())

async with tagentacle_client_transport(node, "mcp_server_node") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        result = await session.call_tool("get_weather", {"city": "Tokyo"})
```

### Server Transport (MCP Server on bus)

```python
from tagentacle_py_core import Node
from tagentacle_py_mcp import tagentacle_server_transport
from mcp.server.lowlevel import Server

mcp_server = Server("my-server")
# ... register tools with @mcp_server.call_tool() ...

node = Node("mcp_server_node")
await node.connect()
spin_task = asyncio.create_task(node.spin())

async with tagentacle_server_transport(node) as (read, write):
    await mcp_server.run(read, write, mcp_server.create_initialization_options())
```

## TagentacleMCPServer (Executable Node)

Built-in MCP Server exposing all bus interactions as MCP Tools:

```python
from tagentacle_py_mcp import TagentacleMCPServer

server = TagentacleMCPServer("bus_tools_node", allowed_topics=["/alerts", "/logs"])
await server.run()
```

### Exposed MCP Tools

| Tool | Description |
|------|-------------|
| `publish_to_topic` | Publish JSON message to a Topic |
| `subscribe_topic` | Subscribe to a Topic and buffer messages |
| `unsubscribe_topic` | Unsubscribe from a Topic |
| `list_nodes` | List all connected nodes |
| `list_topics` | List all active Topics |
| `list_services` | List all registered Services |
| `get_node_info` | Get node details |
| `call_bus_service` | Call any Service via RPC |
| `ping_daemon` | Check Daemon health |
| `describe_topic_schema` | Get Topic message JSON Schema |

## Tagentacle Pkg

This is a Tagentacle **executable pkg** (`type = "executable"` in `tagentacle.toml`) with a library component.

- **Executable**: `TagentacleMCPServer` node (entry point: `tagentacle_py_mcp.server:main`)
- **Library**: Transport adapters importable by other pkgs

Dependencies: `[dependencies] tagentacle = ["tagentacle_py_core"]`

## License

MIT

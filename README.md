# Tagentacle MCP Integration

> **The ROS of AI Agents** — MCPServerNode base class and built-in MCP Server for the Tagentacle bus.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

`tagentacle-py-mcp` provides MCP (Model Context Protocol) integration for the Tagentacle message bus:

- **MCPServerNode** — Base class for building MCP Server Nodes. Runs Streamable HTTP, publishes to `/mcp/directory`.
- **TagentacleMCPServer** — Built-in executable node exposing all bus interactions as MCP Tools.

## Install

```bash
pip install tagentacle-py-mcp
```

This automatically installs `tagentacle-py-core`, `uvicorn`, `starlette`, and `mcp` as dependencies.

## MCPServerNode (Base Class)

Build your own MCP Server Node by subclassing `MCPServerNode`:

```python
from tagentacle_py_mcp import MCPServerNode

class WeatherServer(MCPServerNode):
    def __init__(self):
        super().__init__("weather_server", mcp_port=8100)

    def on_configure(self, config):
        super().on_configure(config)

        @self.mcp.tool(description="Get weather for a city")
        def get_weather(city: str) -> str:
            return f"Sunny in {city}"

async def main():
    node = WeatherServer()
    await node.bringup()
    await node.spin()

asyncio.run(main())
```

On activation the node:
1. Starts a Streamable HTTP server via uvicorn
2. Publishes an `MCPServerDescription` to the `/mcp/directory` Topic
3. Agent Nodes discover and connect via native MCP SDK HTTP client

### Configuration

| Source | Key | Default |
|--------|-----|---------|
| Constructor | `mcp_host` / `mcp_port` | `"0.0.0.0"` / `8000` |
| Environment | `MCP_HOST` / `MCP_PORT` | overrides constructor |

## TagentacleMCPServer (Executable Node)

Built-in MCP Server exposing all bus interactions as MCP Tools:

```python
from tagentacle_py_mcp import TagentacleMCPServer

server = TagentacleMCPServer("bus_tools_node", allowed_topics=["/alerts", "/logs"])
await server.bringup()
await server.spin()
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
- **Library**: `MCPServerNode` base class importable by other pkgs

Dependencies: `[dependencies] tagentacle = ["tagentacle_py_core"]`

## License

MIT

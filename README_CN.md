# Tagentacle MCP 集成

> **The ROS of AI Agents** — Tagentacle 消息总线的 MCP 传输层和内置 MCP Server。

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

`tagentacle-py-mcp` 为 Tagentacle 消息总线提供 MCP（Model Context Protocol）集成：

- **传输层适配器** — 将 MCP JSON-RPC 会话桥接到 Tagentacle 总线（`tagentacle_client_transport`、`tagentacle_server_transport`）。
- **TagentacleMCPServer** — 内置可执行节点，将所有总线交互能力暴露为 MCP Tool。

## 安装

```bash
pip install tagentacle-py-mcp
```

自动安装 `tagentacle-py-core` 作为依赖。

## 传输层适配器（Library）

### 客户端传输（Agent → MCP Server）

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

### 服务端传输（MCP Server 挂载到总线）

```python
from tagentacle_py_core import Node
from tagentacle_py_mcp import tagentacle_server_transport
from mcp.server.lowlevel import Server

mcp_server = Server("my-server")
# ... 使用 @mcp_server.call_tool() 注册工具 ...

node = Node("mcp_server_node")
await node.connect()
spin_task = asyncio.create_task(node.spin())

async with tagentacle_server_transport(node) as (read, write):
    await mcp_server.run(read, write, mcp_server.create_initialization_options())
```

## TagentacleMCPServer（可执行节点）

内置 MCP Server，将所有总线交互能力暴露为 MCP Tool：

```python
from tagentacle_py_mcp import TagentacleMCPServer

server = TagentacleMCPServer("bus_tools_node", allowed_topics=["/alerts", "/logs"])
await server.run()
```

### 暴露的 MCP Tool

| 工具 | 说明 |
|------|------|
| `publish_to_topic` | 向 Topic 发布 JSON 消息 |
| `subscribe_topic` | 订阅 Topic 并缓冲消息 |
| `unsubscribe_topic` | 取消订阅 |
| `list_nodes` | 列出所有连接节点 |
| `list_topics` | 列出所有活跃 Topic |
| `list_services` | 列出所有已注册 Service |
| `get_node_info` | 获取节点详情 |
| `call_bus_service` | 通过 RPC 调用总线上的任意 Service |
| `ping_daemon` | 检查 Daemon 健康状态 |
| `describe_topic_schema` | 获取 Topic 消息 JSON Schema |

## Tagentacle Pkg

这是一个 Tagentacle **executable pkg**（`tagentacle.toml` 中 `type = "executable"`），同时包含 library 组件。

- **Executable**：`TagentacleMCPServer` 节点（入口：`tagentacle_py_mcp.server:main`）
- **Library**：传输层适配器，可被其他 pkg import

依赖：`[dependencies] tagentacle = ["tagentacle_py_core"]`

## 许可证

MIT

"""
Tagentacle MCP Integration: MCPServerNode base class and built-in bus tools server.

This package provides:
  - MCPServerNode: Abstract base class for MCP Server Nodes that run a
    Streamable HTTP endpoint and publish to /mcp/directory for discovery.
  - TagentacleMCPServer: Built-in MCP Server exposing bus operations as MCP Tools.
  - MCP_DIRECTORY_TOPIC: Standard topic name for MCP server discovery.
"""

from tagentacle_py_mcp.server import (
    MCPServerNode,
    TagentacleMCPServer,
    MCP_DIRECTORY_TOPIC,
)

__all__ = [
    "MCPServerNode",
    "TagentacleMCPServer",
    "MCP_DIRECTORY_TOPIC",
]

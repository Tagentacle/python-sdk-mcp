"""
Tagentacle MCP Integration: Transport layer and built-in MCP Server.

This package provides:
  - Transport adapters that bridge MCP JSON-RPC sessions over the Tagentacle bus.
  - TagentacleMCPServer: built-in executable node exposing all bus interactions as MCP Tools.
"""

from tagentacle_py_mcp.transport import (
    tagentacle_client_transport,
    tagentacle_server_transport,
    TagentacleClientTransport,
    TagentacleServerTransport,
    MCP_TRAFFIC_TOPIC,
)
from tagentacle_py_mcp.server import TagentacleMCPServer

__all__ = [
    "tagentacle_client_transport",
    "tagentacle_server_transport",
    "TagentacleClientTransport",
    "TagentacleServerTransport",
    "TagentacleMCPServer",
    "MCP_TRAFFIC_TOPIC",
]

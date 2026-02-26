"""
Tagentacle MCP Server: Built-in MCP Server exposing all bus interactions as MCP Tools.

This node acts as the AI Agent's interface to the Tagentacle bus, wrapping
core bus primitives (publish, subscribe, service calls, introspection) into
standard MCP Tool calls. Agents interact with the entire bus through this
single MCP Server without needing to know the bus protocol.

Usage:
    server = TagentacleMCPServer("bus_tools_node", allowed_topics=["/alerts", "/logs"])
    await server.run()

    # Or as a CLI entrypoint (via tagentacle.toml entry_points):
    python -m tagentacle_py_mcp.server
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from tagentacle_py_core import Node

logger = logging.getLogger("tagentacle.mcp.server")


class TagentacleMCPServer:
    """Built-in MCP Server Node exposing all bus interaction capabilities as MCP Tools.

    Provides MCP Tools for:
      - publish_to_topic: Publish JSON messages to any Topic
      - subscribe_topic: Subscribe to a Topic and start receiving messages
      - unsubscribe_topic: Unsubscribe from a Topic
      - list_nodes: List all connected nodes (via /tagentacle/list_nodes)
      - list_topics: List all active Topics (via /tagentacle/list_topics)
      - list_services: List all registered Services (via /tagentacle/list_services)
      - get_node_info: Get node details (via /tagentacle/get_node_info)
      - call_bus_service: Call any Service on the bus via RPC
      - ping_daemon: Check Daemon health (via /tagentacle/ping)
      - describe_topic_schema: Get JSON Schema for a Topic
    """

    def __init__(self, node_id: str = "tagentacle_mcp_server",
                 allowed_topics: Optional[List[str]] = None):
        """
        Args:
            node_id: Node ID for this server on the Tagentacle bus.
            allowed_topics: If set, only allow publishing to these topic prefixes.
                           If None, all topics are allowed.
        """
        self.node = Node(node_id)
        self.allowed_topics = allowed_topics
        self._subscribed_topics: Dict[str, List[Dict[str, Any]]] = {}  # topic -> [messages]
        self._tools = self._build_tool_definitions()

    def _build_tool_definitions(self) -> List[Dict[str, Any]]:
        """Build MCP tool definitions for all bus interaction capabilities."""
        return [
            {
                "name": "publish_to_topic",
                "description": "Publish a JSON message to a Tagentacle bus Topic. "
                               "Other nodes subscribed to that topic will receive the message.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The topic path to publish to (e.g., '/chat/input')"
                        },
                        "payload": {
                            "type": "object",
                            "description": "The JSON payload to publish"
                        }
                    },
                    "required": ["topic", "payload"]
                }
            },
            {
                "name": "subscribe_topic",
                "description": "Subscribe to a Tagentacle bus Topic and start receiving messages. "
                               "Messages will be buffered and can be retrieved later.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The topic path to subscribe to (e.g., '/chat/output')"
                        }
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "unsubscribe_topic",
                "description": "Unsubscribe from a previously subscribed Topic and clear its message buffer.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The topic path to unsubscribe from"
                        }
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "list_nodes",
                "description": "List all nodes currently connected to the Tagentacle Daemon.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "list_topics",
                "description": "List all active Topics on the Tagentacle bus.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "list_services",
                "description": "List all registered Services on the Tagentacle bus.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_node_info",
                "description": "Get detailed information about a specific node.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "The node_id to query"
                        }
                    },
                    "required": ["node_id"]
                }
            },
            {
                "name": "call_bus_service",
                "description": "Call any Service on the Tagentacle bus via RPC and return the response.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "service": {
                            "type": "string",
                            "description": "The service name to call (e.g., '/math/add')"
                        },
                        "payload": {
                            "type": "object",
                            "description": "The request payload to send"
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Timeout in seconds (default: 30)"
                        }
                    },
                    "required": ["service", "payload"]
                }
            },
            {
                "name": "ping_daemon",
                "description": "Check if the Tagentacle Daemon is healthy and responsive.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "describe_topic_schema",
                "description": "Get the JSON Schema definition for a Topic's message format. "
                               "Useful for LLMs to understand payload structure before publishing.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The topic path to query schema for"
                        }
                    },
                    "required": ["topic"]
                }
            },
        ]

    async def start(self):
        """Connect to bus and register MCP RPC service."""
        await self.node.connect()
        rpc_service = f"/mcp/{self.node.node_id}/rpc"

        @self.node.service(rpc_service)
        async def handle_rpc(payload: Dict[str, Any]):
            return await self._handle_jsonrpc(payload)

        logger.info(f"Tagentacle MCP Server ready on {rpc_service}")
        logger.info(f"Available tools: {[t['name'] for t in self._tools]}")

    async def run(self):
        """Start and spin (blocking)."""
        await self.start()
        await self.node.spin()

    # --- JSON-RPC dispatch ---

    async def _handle_jsonrpc(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process inbound JSON-RPC requests (MCP protocol)."""
        method = payload.get("method", "")
        rpc_id = payload.get("id")
        params = payload.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False}
                    },
                    "serverInfo": {
                        "name": "tagentacle-mcp-server",
                        "version": "0.1.0"
                    }
                }
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {"tools": self._tools}
            }

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            return await self._call_tool(rpc_id, tool_name, arguments)

        elif method == "notifications/initialized":
            return None

        else:
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    # --- Tool dispatch ---

    async def _call_tool(self, rpc_id, tool_name: str, arguments: dict) -> Dict[str, Any]:
        """Execute an MCP tool call."""
        try:
            handler = getattr(self, f"_tool_{tool_name}", None)
            if handler is None:
                return self._error_response(rpc_id, -32601, f"Unknown tool: {tool_name}")
            result_text = await handler(arguments)
            return self._success_response(rpc_id, result_text)
        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}")
            return self._error_result_response(rpc_id, str(e))

    # --- Individual tool implementations ---

    async def _tool_publish_to_topic(self, arguments: dict) -> str:
        topic = arguments.get("topic", "")
        payload = arguments.get("payload", {})

        if self.allowed_topics is not None:
            if not any(topic.startswith(prefix) for prefix in self.allowed_topics):
                raise ValueError(f"Topic '{topic}' is not in the allow-list. "
                               f"Allowed prefixes: {self.allowed_topics}")

        await self.node.publish(topic, payload)
        return f"Published to '{topic}' successfully."

    async def _tool_subscribe_topic(self, arguments: dict) -> str:
        topic = arguments.get("topic", "")

        if topic in self._subscribed_topics:
            count = len(self._subscribed_topics[topic])
            return f"Already subscribed to '{topic}'. {count} buffered message(s)."

        self._subscribed_topics[topic] = []

        @self.node.subscribe(topic)
        async def _on_message(msg):
            self._subscribed_topics.setdefault(topic, []).append({
                "sender": msg.get("sender"),
                "payload": msg.get("payload"),
            })

        return f"Subscribed to '{topic}'. Messages will be buffered."

    async def _tool_unsubscribe_topic(self, arguments: dict) -> str:
        topic = arguments.get("topic", "")

        if topic not in self._subscribed_topics:
            return f"Not subscribed to '{topic}'."

        count = len(self._subscribed_topics.pop(topic, []))
        # Remove callbacks from node subscriber list
        self.node.subscribers.pop(topic, None)
        return f"Unsubscribed from '{topic}'. Cleared {count} buffered message(s)."

    async def _tool_list_nodes(self, arguments: dict) -> str:
        try:
            result = await self.node.call_service("/tagentacle/list_nodes", {}, timeout=10.0)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except asyncio.TimeoutError:
            return "Error: Daemon did not respond to /tagentacle/list_nodes (timeout)."

    async def _tool_list_topics(self, arguments: dict) -> str:
        try:
            result = await self.node.call_service("/tagentacle/list_topics", {}, timeout=10.0)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except asyncio.TimeoutError:
            return "Error: Daemon did not respond to /tagentacle/list_topics (timeout)."

    async def _tool_list_services(self, arguments: dict) -> str:
        try:
            result = await self.node.call_service("/tagentacle/list_services", {}, timeout=10.0)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except asyncio.TimeoutError:
            return "Error: Daemon did not respond to /tagentacle/list_services (timeout)."

    async def _tool_get_node_info(self, arguments: dict) -> str:
        node_id = arguments.get("node_id", "")
        try:
            result = await self.node.call_service(
                "/tagentacle/get_node_info", {"node_id": node_id}, timeout=10.0
            )
            return json.dumps(result, ensure_ascii=False, indent=2)
        except asyncio.TimeoutError:
            return f"Error: Daemon did not respond to /tagentacle/get_node_info for '{node_id}' (timeout)."

    async def _tool_call_bus_service(self, arguments: dict) -> str:
        service = arguments.get("service", "")
        payload = arguments.get("payload", {})
        timeout = arguments.get("timeout", 30.0)
        try:
            result = await self.node.call_service(service, payload, timeout=timeout)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except asyncio.TimeoutError:
            return f"Error: Service '{service}' did not respond within {timeout}s."

    async def _tool_ping_daemon(self, arguments: dict) -> str:
        try:
            result = await self.node.call_service("/tagentacle/ping", {}, timeout=5.0)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except asyncio.TimeoutError:
            return "Error: Daemon did not respond to /tagentacle/ping (timeout)."

    async def _tool_describe_topic_schema(self, arguments: dict) -> str:
        topic = arguments.get("topic", "")
        try:
            result = await self.node.call_service(
                "/tagentacle/describe_topic_schema", {"topic": topic}, timeout=10.0
            )
            return json.dumps(result, ensure_ascii=False, indent=2)
        except asyncio.TimeoutError:
            return f"Error: Daemon did not respond to /tagentacle/describe_topic_schema for '{topic}' (timeout)."

    # --- Response helpers ---

    @staticmethod
    def _success_response(rpc_id, text: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "content": [{"type": "text", "text": text}]
            }
        }

    @staticmethod
    def _error_result_response(rpc_id, error_text: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "content": [{"type": "text", "text": f"Error: {error_text}"}],
                "isError": True
            }
        }

    @staticmethod
    def _error_response(rpc_id, code: int, message: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": code, "message": message}
        }


async def main():
    """Standalone entrypoint for the Tagentacle MCP Server."""
    import sys
    logging.basicConfig(level=logging.INFO)

    allowed = None
    if len(sys.argv) > 1:
        allowed = sys.argv[1:]
        logger.info(f"Topic allow-list: {allowed}")

    server = TagentacleMCPServer(allowed_topics=allowed)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

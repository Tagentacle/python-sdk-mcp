"""
Tagentacle MCP Server: Built-in MCP Server exposing all bus interactions as MCP Tools.

This node acts as the AI Agent's interface to the Tagentacle bus, wrapping
core bus primitives (publish, subscribe, service calls, introspection) into
standard MCP Tool calls.  Agents interact with the entire bus through this
single MCP Server without needing to know the bus protocol.

Powered by the official Anthropic MCP SDK (``FastMCP``).  Tool schemas are
auto-generated from Python type-hints — no hand-written JSON-Schema needed.

Usage:
    server = TagentacleMCPServer("bus_tools_node", allowed_topics=["/alerts", "/logs"])
    await server.run()

    # Or as a CLI entrypoint (via tagentacle.toml entry_points):
    python -m tagentacle_py_mcp.server
"""

import asyncio
import json
import logging
from typing import Annotated, Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field
from tagentacle_py_core import Node

from tagentacle_py_mcp.transport import tagentacle_server_transport

logger = logging.getLogger("tagentacle.mcp.server")


class TagentacleMCPServer:
    """Built-in MCP Server Node exposing all bus interactions as MCP Tools.

    Uses ``FastMCP`` for tool registration and JSON-RPC protocol handling,
    with ``tagentacle_server_transport`` bridging MCP sessions over the
    Tagentacle bus.
    """

    def __init__(
        self,
        node_id: str = "tagentacle_mcp_server",
        allowed_topics: Optional[List[str]] = None,
    ):
        """
        Args:
            node_id: Node ID for this server on the Tagentacle bus.
            allowed_topics: If set, only allow publishing to these topic prefixes.
                           If None, all topics are allowed.
        """
        self.node = Node(node_id)
        self.allowed_topics = allowed_topics
        self._subscribed_topics: Dict[str, List[Dict[str, Any]]] = {}

        self.mcp = FastMCP(
            name="tagentacle-mcp-server",
            instructions=(
                "Tagentacle bus interaction server.  Use these tools to publish "
                "messages, subscribe to topics, call services, and introspect "
                "the running system."
            ),
        )
        self._register_tools()

    # ------------------------------------------------------------------
    # Tool registration  (schemas derived from type-hints automatically)
    # ------------------------------------------------------------------

    def _register_tools(self) -> None:  # noqa: C901 — intentionally flat
        """Register all bus interaction tools with ``FastMCP``."""

        # --- pub / sub ---

        @self.mcp.tool(
            description=(
                "Publish a JSON message to a Tagentacle bus Topic.  "
                "Other nodes subscribed to that topic will receive the message."
            ),
        )
        async def publish_to_topic(
            topic: Annotated[str, Field(description="Topic path, e.g. '/chat/input'")],
            payload: Annotated[dict, Field(description="JSON payload to publish")],
        ) -> str:
            if self.allowed_topics is not None:
                if not any(topic.startswith(p) for p in self.allowed_topics):
                    raise ValueError(
                        f"Topic '{topic}' not in allow-list: {self.allowed_topics}"
                    )
            await self.node.publish(topic, payload)
            return f"Published to '{topic}' successfully."

        @self.mcp.tool(
            description=(
                "Subscribe to a Tagentacle bus Topic and start buffering "
                "incoming messages."
            ),
        )
        async def subscribe_topic(
            topic: Annotated[str, Field(description="Topic path, e.g. '/chat/output'")],
        ) -> str:
            if topic in self._subscribed_topics:
                n = len(self._subscribed_topics[topic])
                return f"Already subscribed to '{topic}'. {n} buffered message(s)."

            self._subscribed_topics[topic] = []

            @self.node.subscribe(topic)
            async def _on_message(msg):
                self._subscribed_topics.setdefault(topic, []).append({
                    "sender": msg.get("sender"),
                    "payload": msg.get("payload"),
                })

            return f"Subscribed to '{topic}'. Messages will be buffered."

        @self.mcp.tool(
            description="Unsubscribe from a Topic and clear its message buffer.",
        )
        async def unsubscribe_topic(
            topic: Annotated[str, Field(description="Topic path to unsubscribe from")],
        ) -> str:
            if topic not in self._subscribed_topics:
                return f"Not subscribed to '{topic}'."
            count = len(self._subscribed_topics.pop(topic, []))
            self.node.subscribers.pop(topic, None)
            return f"Unsubscribed from '{topic}'. Cleared {count} buffered message(s)."

        # --- introspection ---

        @self.mcp.tool(
            description="List all nodes currently connected to the Tagentacle Daemon.",
        )
        async def list_nodes() -> str:
            return await self._daemon_query("/tagentacle/list_nodes")

        @self.mcp.tool(
            description="List all active Topics on the Tagentacle bus.",
        )
        async def list_topics() -> str:
            return await self._daemon_query("/tagentacle/list_topics")

        @self.mcp.tool(
            description="List all registered Services on the Tagentacle bus.",
        )
        async def list_services() -> str:
            return await self._daemon_query("/tagentacle/list_services")

        @self.mcp.tool(
            description="Get detailed information about a specific node.",
        )
        async def get_node_info(
            node_id: Annotated[str, Field(description="The node_id to query")],
        ) -> str:
            return await self._daemon_query(
                "/tagentacle/get_node_info", {"node_id": node_id}
            )

        @self.mcp.tool(
            description=(
                "Get the JSON Schema definition for a Topic's message format.  "
                "Useful for understanding payload structure before publishing."
            ),
        )
        async def describe_topic_schema(
            topic: Annotated[str, Field(description="Topic path to query schema for")],
        ) -> str:
            return await self._daemon_query(
                "/tagentacle/describe_topic_schema", {"topic": topic}
            )

        # --- generic service call ---

        @self.mcp.tool(
            description="Call any Service on the Tagentacle bus via RPC and return the response.",
        )
        async def call_bus_service(
            service: Annotated[str, Field(description="Service name, e.g. '/math/add'")],
            payload: Annotated[dict, Field(description="Request payload")],
            timeout: Annotated[float, Field(description="Timeout in seconds")] = 30.0,
        ) -> str:
            try:
                result = await self.node.call_service(service, payload, timeout=timeout)
                return json.dumps(result, ensure_ascii=False, indent=2)
            except asyncio.TimeoutError:
                return f"Error: Service '{service}' did not respond within {timeout}s."

        # --- health ---

        @self.mcp.tool(
            description="Check if the Tagentacle Daemon is healthy and responsive.",
        )
        async def ping_daemon() -> str:
            return await self._daemon_query("/tagentacle/ping", timeout=5.0)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _daemon_query(
        self, service: str, payload: Optional[dict] = None, *, timeout: float = 10.0
    ) -> str:
        """Call a Daemon introspection service and return pretty-printed JSON."""
        try:
            result = await self.node.call_service(
                service, payload or {}, timeout=timeout
            )
            return json.dumps(result, ensure_ascii=False, indent=2)
        except asyncio.TimeoutError:
            return f"Error: Daemon did not respond to {service} (timeout)."

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Connect to bus and run the MCP server over bus transport (blocking)."""
        await self.node.connect()
        logger.info("Tagentacle MCP Server starting on bus …")

        async with tagentacle_server_transport(self.node) as (read_stream, write_stream):
            await self.mcp._mcp_server.run(
                read_stream,
                write_stream,
                self.mcp._mcp_server.create_initialization_options(),
            )



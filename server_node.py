"""Thin entry point for the Tagentacle built-in MCP Server node.

This file is the *executable* wrapper — the library lives in
``tagentacle_py_mcp/``.  It should be referenced by ``tagentacle.toml``
as the package's runnable entry.

Launches TagentacleMCPServer as a LifecycleNode with Streamable HTTP.
"""

import asyncio
import logging
import os
import sys

from tagentacle_py_mcp.server import TagentacleMCPServer


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("tagentacle.mcp.server")

    allowed = None
    if len(sys.argv) > 1:
        allowed = sys.argv[1:]
        logger.info(f"Topic allow-list: {allowed}")

    mcp_port = int(os.environ.get("MCP_PORT", "8000"))

    server = TagentacleMCPServer(mcp_port=mcp_port, allowed_topics=allowed)
    await server.connect()
    spin_task = asyncio.create_task(server.spin())

    await server.configure()
    await server.activate()

    await spin_task


if __name__ == "__main__":
    asyncio.run(main())

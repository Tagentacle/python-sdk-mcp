"""Thin entry point for the Tagentacle built-in MCP Server node.

This file is the *executable* wrapper — the library lives in
``tagentacle_py_mcp/``.  It should be referenced by ``tagentacle.toml``
as the package's runnable entry.
"""

import asyncio
import logging
import sys

from tagentacle_py_mcp.server import TagentacleMCPServer


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("tagentacle.mcp.server")

    allowed = None
    if len(sys.argv) > 1:
        allowed = sys.argv[1:]
        logger.info(f"Topic allow-list: {allowed}")

    server = TagentacleMCPServer(allowed_topics=allowed)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

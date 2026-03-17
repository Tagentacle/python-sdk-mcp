"""Thin entry point for the TACL Authority node.

Launches TACLAuthority as a LifecycleNode with Streamable HTTP.
This is the TACL credential issuer — agents connect here to authenticate
and receive JWT credentials for accessing other auth-enabled MCP servers.

Requires: ``pip install tagentacle-py-tacl[authority]``
"""

import asyncio
import logging
import os
import sys


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("tagentacle.tacl.authority")

    try:
        from tagentacle_py_tacl.authority import TACLAuthority
    except ImportError as exc:
        logger.error(
            "Failed to import TACLAuthority: %s\n"
            "Install with: uv pip install tagentacle-py-tacl[authority]",
            exc,
        )
        sys.exit(1)

    mcp_port = int(os.environ.get("MCP_PORT", "8200"))
    db_path = os.environ.get("TAGENTACLE_PERMISSION_DB", "permission.db")

    server = TACLAuthority(mcp_port=mcp_port, db_path=db_path)
    await server.connect()
    spin_task = asyncio.create_task(server.spin())

    await server.configure()
    await server.activate()

    await spin_task


if __name__ == "__main__":
    asyncio.run(main())

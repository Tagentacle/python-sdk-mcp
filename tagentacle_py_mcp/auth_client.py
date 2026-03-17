"""
Backward-compatibility shim — TACL auth client has moved to ``tagentacle-py-tacl``.

Re-exported from ``tagentacle_py_tacl.client``.
"""

from tagentacle_py_tacl.client import AuthMCPClient  # noqa: F401

__all__ = ["AuthMCPClient"]

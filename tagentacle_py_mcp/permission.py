"""
Backward-compatibility shim — PermissionMCPServerNode has moved to
``tagentacle-py-tacl`` as ``TACLAuthority``.

Requires: ``pip install tagentacle-py-tacl[authority]``
"""

from tagentacle_py_tacl.authority import (  # noqa: F401
    TACLAuthority,
    PermissionMCPServerNode,  # backward compat alias
)

__all__ = ["PermissionMCPServerNode", "TACLAuthority"]

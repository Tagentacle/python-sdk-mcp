"""
Backward-compatibility shim — TACL auth has moved to ``tagentacle-py-tacl``.

All public APIs are re-exported from ``tagentacle_py_tacl.auth``.
"""

# Re-export everything so existing ``from tagentacle_py_mcp.auth import ...``
# continues to work.
from tagentacle_py_tacl.auth import (  # noqa: F401
    AuthError,
    CallerIdentity,
    CredentialInvalid,
    ToolNotAuthorized,
    check_tool_authorized,
    get_caller_identity,
    set_caller_identity,
    sign_credential,
    verify_credential,
)

__all__ = [
    "CallerIdentity",
    "AuthError",
    "CredentialInvalid",
    "ToolNotAuthorized",
    "sign_credential",
    "verify_credential",
    "check_tool_authorized",
    "get_caller_identity",
    "set_caller_identity",
]

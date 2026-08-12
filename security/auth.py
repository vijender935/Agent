"""
Simple Bearer token check for HTTP MCP mode.
"""

from __future__ import annotations

from config.settings import AGENT_API_TOKEN


def is_auth_required() -> bool:
    return bool(AGENT_API_TOKEN)


def verify_bearer(authorization_header: str | None) -> bool:
    """
    Return True if the request is allowed.
    If AGENT_API_TOKEN is empty, everything is allowed (dev mode).
    """
    if not AGENT_API_TOKEN:
        return True
    if not authorization_header:
        return False
    parts = authorization_header.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False
    return parts[1].strip() == AGENT_API_TOKEN

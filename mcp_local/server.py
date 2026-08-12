"""
MCP Server for the Local Agent (Grok Custom Connector).

Supports:
  - stdio (default)
  - streamable-http (for remote / Grok)

AUTH IS HARD-DISABLED.
Grok's Custom Connector UI currently only supports OAuth and shows an
OAuth credentials form whenever the server returns 401 or advertises auth.
Plain Bearer token is not offered in the UI. For personal tunnel use we
therefore never challenge the client (no 401, no WWW-Authenticate).

Fixes applied:
  1. Folder named "mcp_local" (not "mcp") to avoid shadowing the installed
     "mcp" package on sys.path.
  2. Pin "mcp<2.0.0" in requirements.txt.
  3. TransportSecuritySettings(enable_dns_rebinding_protection=False) so
     tunnel hosts (trycloudflare.com etc.) are accepted.
  4. Auth middleware is a no-op so Grok never sees an auth challenge.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any

# Project root on path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server.transport_security import TransportSecuritySettings
except ImportError:
    try:
        from mcp.server import FastMCP  # type: ignore
        from mcp.server.transport_security import TransportSecuritySettings
    except ImportError as e:
        print("ERROR: 'mcp' package not found.\nInstall with: pip install \"mcp<2\"", file=sys.stderr)
        raise SystemExit(1) from e

from config.settings import (
    AGENT_API_TOKEN,
    REQUIRE_CONFIRMATION_REMOTE,
    WORKSPACE,
)
from core.safety import is_risky_command
from core.tools import execute_tool, tool_names
from security.audit import log_tool_call
# Auth HARD-DISABLED for Grok custom connector compatibility.
# Grok UI only supports OAuth for custom connectors; any 401 triggers the form.
# from security.auth import verify_bearer

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "LocalAgent",
    instructions=(
        "You are talking to a sandboxed local agent. "
        f"All file and shell operations are restricted to the workspace: {WORKSPACE}. "
        "Destructive actions (delete, rm, package installs, etc.) should be used carefully. "
        "Prefer relative paths."
    ),
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)


def _run(name: str, args: dict[str, Any], *, source: str = "mcp") -> dict[str, Any]:
    """Execute tool + audit + optional remote confirmation policy."""
    # Remote safety: block destructive tools if configured
    if REQUIRE_CONFIRMATION_REMOTE:
        if name == "delete_path":
            return {
                "success": False,
                "error": (
                    "Remote delete is disabled (REQUIRE_CONFIRMATION_REMOTE=true). "
                    "Set it to false or use the local agent."
                ),
            }
        if name == "run_command" and is_risky_command(str(args.get("command", ""))):
            return {
                "success": False,
                "error": (
                    "Remote risky command is disabled (REQUIRE_CONFIRMATION_REMOTE=true)."
                ),
            }

    t0 = time.perf_counter()
    result = execute_tool(name, args)
    duration = (time.perf_counter() - t0) * 1000
    log_tool_call(name, args, result, source=source, duration_ms=round(duration, 1))
    return result


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_files(path: str = ".") -> dict[str, Any]:
    """List files and folders inside a directory (non-recursive)."""
    return _run("list_files", {"path": path})


@mcp.tool()
def create_folder(name: str) -> dict[str, Any]:
    """Create a new folder (parents created automatically)."""
    return _run("create_folder", {"name": name})


@mcp.tool()
def create_file(path: str, content: str = "") -> dict[str, Any]:
    """Create a new text file (overwrites if it already exists)."""
    return _run("create_file", {"path": path, "content": content})


@mcp.tool()
def read_file(path: str) -> dict[str, Any]:
    """Read the full content of a text file (size limited)."""
    return _run("read_file", {"path": path})


@mcp.tool()
def write_file(path: str, content: str) -> dict[str, Any]:
    """Overwrite an existing text file. Use create_file for new files."""
    return _run("write_file", {"path": path, "content": content})


@mcp.tool()
def copy_file(source: str, destination: str) -> dict[str, Any]:
    """Copy a file to another location inside the workspace."""
    return _run("copy_file", {"source": source, "destination": destination})


@mcp.tool()
def move_file(source: str, destination: str) -> dict[str, Any]:
    """Move or rename a file/folder inside the workspace."""
    return _run("move_file", {"source": source, "destination": destination})


@mcp.tool()
def delete_path(path: str) -> dict[str, Any]:
    """
    Delete a file or folder (recursive for directories).
    Use with extreme care.
    """
    return _run("delete_path", {"path": path})


@mcp.tool()
def run_command(command: str, timeout: int = 30) -> dict[str, Any]:
    """
    Execute a shell command inside the agent workspace.
    Output is truncated. Timeout is clamped (max 90s).
    """
    return _run("run_command", {"command": command, "timeout": timeout})


@mcp.tool()
def get_clipboard() -> dict[str, Any]:
    """Read the current Android/Termux clipboard content."""
    return _run("get_clipboard", {})


@mcp.tool()
def set_clipboard(text: str) -> dict[str, Any]:
    """Write text to the Android/Termux clipboard."""
    return _run("set_clipboard", {"text": text})


@mcp.tool()
def agent_status() -> str:
    """Return basic status of the agent and its workspace."""
    names = ", ".join(tool_names())
    # Auth is hard-disabled so Grok does not show the OAuth form.
    auth = "DISABLED (forced off for Grok compatibility)"
    return (
        f"Agent is online.\n"
        f"Workspace: {WORKSPACE}\n"
        f"Auth: {auth}\n"
        f"Tools: {names}"
    )


# ---------------------------------------------------------------------------
# Bearer-token enforcement — HARD DISABLED
# ---------------------------------------------------------------------------
# Grok Custom Connector UI currently only offers an OAuth credentials form.
# Returning any 401 (or advertising auth) makes Grok show that form and
# blocks plain connection. For personal / tunnel use we therefore never
# challenge the client. The old middleware is kept as a no-op so the rest
# of the startup path stays identical.

class _BearerAuthMiddleware:
    """No-op middleware. Auth is forced off so Grok does not request OAuth."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Always pass through — never return 401.
        await self.app(scope, receive, send)


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Local Agent MCP Server")
    parser.add_argument("--http", action="store_true", help="Use streamable-http transport")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port")
    args = parser.parse_args()

    if args.http:
        print(f"Starting MCP server (streamable-http) on http://{args.host}:{args.port}")
        print(f"Workspace : {WORKSPACE}")
        print("Auth     : HARD-DISABLED (Grok compatibility — no OAuth / no Bearer challenge)")
        print("Note     : Put this behind a tunnel only for short trusted sessions.")
        if AGENT_API_TOKEN:
            print("Note     : AGENT_API_TOKEN is present in .env but is IGNORED.")

        # Preferred path: build the ASGI app ourselves so we can wrap it
        # with the auth middleware above, and control host/port directly
        # via uvicorn (avoids relying on FastMCP.run()'s host/port kwargs,
        # which have changed across mcp SDK versions).
        try:
            app = mcp.streamable_http_app()
        except Exception as e:  # pragma: no cover - defensive fallback
            print(f"Note     : streamable_http_app() unavailable ({e}); "
                  f"falling back to mcp.run() (auth NOT enforced in this path).",
                  file=sys.stderr)
            app = None

        if app is not None:
            app = _BearerAuthMiddleware(app)
            import uvicorn
            uvicorn.run(app, host=args.host, port=args.port)
        else:
            try:
                mcp.run(transport="streamable-http", host=args.host, port=args.port)
            except TypeError:
                os.environ["MCP_HOST"] = args.host
                os.environ["MCP_PORT"] = str(args.port)
                mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

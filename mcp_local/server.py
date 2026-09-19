"""Cloud-hosted MCP server for the Agent.

Provides a streamable HTTP MCP endpoint suitable for Render and remote MCP clients.
Authentication is intentionally not used; protect the service with your deployment
network controls if you expose it publicly.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server.transport_security import TransportSecuritySettings
except ImportError:
    from mcp.server import FastMCP  # type: ignore
    from mcp.server.transport_security import TransportSecuritySettings

from config.settings import WORKSPACE
from core.tools import execute_tool, tool_names
from security.audit import log_tool_call

mcp = FastMCP(
    "Agent",
    instructions=(
        "You are connected to a cloud-hosted agent. "
        f"File and shell operations are restricted to the workspace: {WORKSPACE}. "
        "Use destructive operations carefully."
    ),
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


def _run(name: str, args: dict[str, Any], *, source: str = "mcp") -> dict[str, Any]:
    started = time.perf_counter()
    result = execute_tool(name, args)
    duration = (time.perf_counter() - started) * 1000
    log_tool_call(name, args, result, source=source, duration_ms=round(duration, 1))
    return result


@mcp.tool()
def list_files(path: str = ".") -> dict[str, Any]:
    """List files and folders in the agent workspace."""
    return _run("list_files", {"path": path})

@mcp.tool()
def create_folder(name: str) -> dict[str, Any]:
    """Create a folder in the agent workspace."""
    return _run("create_folder", {"name": name})

@mcp.tool()
def create_file(path: str, content: str = "") -> dict[str, Any]:
    """Create or replace a text file in the agent workspace."""
    return _run("create_file", {"path": path, "content": content})

@mcp.tool()
def read_file(path: str) -> dict[str, Any]:
    """Read a text file from the agent workspace."""
    return _run("read_file", {"path": path})

@mcp.tool()
def write_file(path: str, content: str) -> dict[str, Any]:
    """Overwrite an existing text file in the agent workspace."""
    return _run("write_file", {"path": path, "content": content})

@mcp.tool()
def copy_file(source: str, destination: str) -> dict[str, Any]:
    """Copy a file inside the agent workspace."""
    return _run("copy_file", {"source": source, "destination": destination})

@mcp.tool()
def move_file(source: str, destination: str) -> dict[str, Any]:
    """Move or rename a file or folder inside the agent workspace."""
    return _run("move_file", {"source": source, "destination": destination})

@mcp.tool()
def delete_path(path: str) -> dict[str, Any]:
    """Delete a file or folder recursively inside the agent workspace."""
    return _run("delete_path", {"path": path})

@mcp.tool()
def run_command(command: str, timeout: int = 30) -> dict[str, Any]:
    """Run a shell command in the agent workspace."""
    return _run("run_command", {"command": command, "timeout": timeout})

@mcp.tool()
def agent_status() -> str:
    """Return basic agent status and workspace information."""
    return f"Agent is online.\\nWorkspace: {WORKSPACE}\\nAuth: DISABLED\\nTools: {', '.join(tool_names())}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Cloud Agent MCP Server")
    parser.add_argument("--http", action="store_true", help="Use streamable HTTP")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    args = parser.parse_args()
    if not args.http:
        mcp.run(transport="stdio")
        return
    app = mcp.streamable_http_app()
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

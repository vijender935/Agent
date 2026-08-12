#!/usr/bin/env python3
"""Start MCP server for Grok Custom Connector.

Usage:
  python run_mcp_server.py --http --port 8000
"""
import runpy
from pathlib import Path

server = Path(__file__).parent / "mcp_local" / "server.py"
runpy.run_path(str(server), run_name="__main__")

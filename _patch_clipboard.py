from pathlib import Path

p = Path("mcp_local/server.py")
text = p.read_text()

old = '''@mcp.tool()
def run_command(command: str, timeout: int = 30) -> dict[str, Any]:
    """
    Execute a shell command inside the agent workspace.
    Output is truncated. Timeout is clamped (max 90s).
    """
    return _run("run_command", {"command": command, "timeout": timeout})


@mcp.tool()
def agent_status() -> str:'''

new = '''@mcp.tool()
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
def agent_status() -> str:'''

if old in text:
    p.write_text(text.replace(old, new))
    print("OK: clipboard tools added to server.py")
else:
    print("PATTERN NOT FOUND")

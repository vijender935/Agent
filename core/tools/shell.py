"""
Controlled shell command execution inside the workspace.
"""

from __future__ import annotations

import subprocess
from typing import Any

from config.settings import (
    COMMAND_TIMEOUT_DEFAULT,
    COMMAND_TIMEOUT_MAX,
    MAX_COMMAND_OUTPUT,
    WORKSPACE,
)
from core.safety import is_risky_command


def _ok(**kwargs: Any) -> dict[str, Any]:
    return {"success": True, **kwargs}


def _err(msg: str) -> dict[str, Any]:
    return {"success": False, "error": msg}


def run_command(command: str, timeout: int | None = None) -> dict[str, Any]:
    """
    Run a shell command inside the agent workspace.

    Uses shell=True for flexibility. Caller is responsible for confirmation
    of risky commands. Output is truncated. Timeout is clamped.
    """
    command = (command or "").strip()
    if not command:
        return _err("Command is empty.")

    t = timeout if timeout is not None else COMMAND_TIMEOUT_DEFAULT
    t = max(1, min(int(t), COMMAND_TIMEOUT_MAX))

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=t,
            env=None,
        )

        stdout = (result.stdout or "")[-MAX_COMMAND_OUTPUT:]
        stderr = (result.stderr or "")[-MAX_COMMAND_OUTPUT:]

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "command": command,
            "timeout": t,
            "risky": is_risky_command(command),
        }
    except subprocess.TimeoutExpired:
        return _err(f"Command timed out after {t}s: {command}")
    except Exception as e:
        return _err(str(e))

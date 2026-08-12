"""
Clipboard tools for Termux (via termux-api).

Requires on the Termux side:
  1. Install the "Termux:API" Android app from F-Droid / Play Store
  2. pkg install termux-api

These commands are called from inside proot Ubuntu using the full Termux path.
"""

from __future__ import annotations

import subprocess
from typing import Any

# Full paths to Termux binaries (accessible from proot)
TERMUX_PREFIX = "/data/data/com.termux/files/usr/bin"
CLIP_GET = f"{TERMUX_PREFIX}/termux-clipboard-get"
CLIP_SET = f"{TERMUX_PREFIX}/termux-clipboard-set"


def _run_termux(cmd: list[str], input_text: str | None = None) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", "Clipboard command timed out"
    except Exception as e:
        return 1, "", str(e)


def get_clipboard() -> dict[str, Any]:
    """Read the current Android/Termux clipboard content."""
    code, out, err = _run_termux([CLIP_GET])
    if code == 0:
        return {
            "success": True,
            "content": out,
            "length": len(out),
        }
    return {
        "success": False,
        "error": err or f"termux-clipboard-get failed (code {code})",
        "hint": (
            "Install Termux:API app + run: pkg install termux-api"
        ),
    }


def set_clipboard(text: str) -> dict[str, Any]:
    """Write text to the Android/Termux clipboard."""
    if text is None:
        text = ""
    code, out, err = _run_termux([CLIP_SET], input_text=text)
    if code == 0:
        return {
            "success": True,
            "message": "Clipboard updated",
            "length": len(text),
        }
    return {
        "success": False,
        "error": err or f"termux-clipboard-set failed (code {code})",
        "hint": (
            "Install Termux:API app + run: pkg install termux-api"
        ),
    }

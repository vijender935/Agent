"""
Risky command detection.
"""

from __future__ import annotations

from config.settings import RISKY_COMMAND_PATTERNS


def is_risky_command(command: str) -> bool:
    """Heuristic check whether a shell command is potentially destructive."""
    cmd = (command or "").strip().lower()
    if not cmd:
        return False
    return any(pat in cmd for pat in RISKY_COMMAND_PATTERNS)

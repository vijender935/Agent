"""
Simple JSONL audit log for every tool call.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from config.settings import AUDIT_LOG_PATH, WORKSPACE


def log_tool_call(
    tool: str,
    args: dict[str, Any],
    result: dict[str, Any],
    *,
    source: str = "unknown",
    duration_ms: float | None = None,
) -> None:
    if not AUDIT_LOG_PATH:
        return

    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": source,
        "tool": tool,
        "args": _safe_args(args),
        "success": result.get("success"),
        "error": result.get("error"),
        "duration_ms": duration_ms,
    }

    path = Path(AUDIT_LOG_PATH)
    if not path.is_absolute():
        path = WORKSPACE / path

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        # Never crash the agent because of logging
        pass


def _safe_args(args: dict[str, Any]) -> dict[str, Any]:
    """Truncate large content fields so the log stays small."""
    out = {}
    for k, v in args.items():
        if k in ("content",) and isinstance(v, str) and len(v) > 200:
            out[k] = v[:200] + f"... ({len(v)} chars)"
        else:
            out[k] = v
    return out

"""
Interactive confirmation for destructive actions (local agent).
"""

from __future__ import annotations


def ask_confirmation(reason: str) -> bool:
    """Interactive yes/no. Returns True only on explicit yes."""
    print(f"\n⚠️  Confirmation required: {reason}")
    try:
        answer = input("Confirm? (yes/no): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return False
    return answer in ("yes", "y")

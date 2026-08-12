"""
Tool registry – single place that maps names to callables + schemas.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable

from core.tools import clipboard, filesystem, shell

TOOL_MAP: dict[str, Callable[..., dict[str, Any]]] = {
    "list_files": filesystem.list_files,
    "create_folder": filesystem.create_folder,
    "create_file": filesystem.create_file,
    "read_file": filesystem.read_file,
    "write_file": filesystem.write_file,
    "copy_file": filesystem.copy_file,
    "move_file": filesystem.move_file,
    "delete_path": filesystem.delete_path,
    "run_command": shell.run_command,
    "get_clipboard": clipboard.get_clipboard,
    "set_clipboard": clipboard.set_clipboard,
}

# OpenAI / xAI compatible function schemas
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and folders in a directory (non-recursive).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path inside workspace. Default: '.'",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": "Create a new folder (parents are created automatically).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Folder name or relative path"}
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a new text file (overwrites if it already exists).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string", "description": "File content"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full content of a text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Overwrite an existing text file. Use create_file for new files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "copy_file",
            "description": "Copy a file to another location inside the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "destination": {"type": "string"},
                },
                "required": ["source", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": "Move or rename a file/folder inside the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "destination": {"type": "string"},
                },
                "required": ["source", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_path",
            "description": "Delete a file or folder (recursive). Destructive – use carefully.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to delete"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Execute a shell command inside the workspace. "
                "Destructive / system-changing commands should be used only when necessary."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The full shell command to run",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 30, max 90)",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_clipboard",
            "description": "Read the current Android/Termux clipboard content.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_clipboard",
            "description": "Write text to the Android/Termux clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to put on the clipboard",
                    }
                },
                "required": ["text"],
            },
        },
    },
]


def execute_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a tool call and always return a structured dict."""
    func = TOOL_MAP.get(name)
    if func is None:
        return {"success": False, "error": f"Unknown tool: {name}"}

    try:
        sig = inspect.signature(func)
        accepted = set(sig.parameters.keys())
        clean_args = {k: v for k, v in args.items() if k in accepted}
        return func(**clean_args)
    except TypeError as e:
        return {"success": False, "error": f"Invalid arguments for {name}: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_names() -> list[str]:
    return list(TOOL_MAP.keys())

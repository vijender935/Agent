"""
Safe file-system tools restricted to the agent workspace.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from config.settings import MAX_FILE_SIZE_BYTES, WORKSPACE
from core.workspace import PathEscapeError, rel_to_workspace, safe_path


def _ok(**kwargs: Any) -> dict[str, Any]:
    return {"success": True, **kwargs}


def _err(msg: str) -> dict[str, Any]:
    return {"success": False, "error": msg}


def list_files(path: str = ".") -> dict[str, Any]:
    """List files and folders inside a directory (non-recursive)."""
    try:
        folder = safe_path(path)
        if not folder.exists():
            return _err(f"Folder not found: {path}")
        if not folder.is_dir():
            return _err(f"Not a directory: {path}")

        items: list[str] = []
        for item in sorted(folder.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            name = item.name + ("/" if item.is_dir() else "")
            items.append(name)

        return _ok(path=rel_to_workspace(folder), items=items, count=len(items))
    except PathEscapeError as e:
        return _err(str(e))
    except Exception as e:
        return _err(str(e))


def create_folder(name: str) -> dict[str, Any]:
    """Create a folder (and parents if needed)."""
    try:
        if not name or not str(name).strip():
            return _err("Folder name cannot be empty.")
        folder = safe_path(name)
        folder.mkdir(parents=True, exist_ok=True)
        return _ok(message=f"Folder created: {name}", path=rel_to_workspace(folder))
    except PathEscapeError as e:
        return _err(str(e))
    except Exception as e:
        return _err(str(e))


def create_file(path: str, content: str = "") -> dict[str, Any]:
    """Create a new text file (overwrites if it already exists)."""
    try:
        if not path or not str(path).strip():
            return _err("File path cannot be empty.")
        file_path = safe_path(path)
        data = content.encode("utf-8")
        if len(data) > MAX_FILE_SIZE_BYTES:
            return _err(f"Content too large (max {MAX_FILE_SIZE_BYTES} bytes).")

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        return _ok(message=f"File created: {path}", bytes=len(data))
    except PathEscapeError as e:
        return _err(str(e))
    except Exception as e:
        return _err(str(e))


def read_file(path: str) -> dict[str, Any]:
    """Read a text file (size limited)."""
    try:
        file_path = safe_path(path)
        if not file_path.exists():
            return _err(f"File not found: {path}")
        if not file_path.is_file():
            return _err(f"Not a file: {path}")

        size = file_path.stat().st_size
        if size > MAX_FILE_SIZE_BYTES:
            return _err(
                f"File too large ({size} bytes). Max allowed: {MAX_FILE_SIZE_BYTES} bytes."
            )

        content = file_path.read_text(encoding="utf-8", errors="replace")
        return _ok(path=path, content=content, size=size)
    except PathEscapeError as e:
        return _err(str(e))
    except Exception as e:
        return _err(str(e))


def write_file(path: str, content: str) -> dict[str, Any]:
    """Overwrite an existing text file. Use create_file for new files."""
    try:
        file_path = safe_path(path)
        if not file_path.exists():
            return _err(f"File does not exist: {path}. Use create_file instead.")
        if not file_path.is_file():
            return _err(f"Not a file: {path}")
        data = content.encode("utf-8")
        if len(data) > MAX_FILE_SIZE_BYTES:
            return _err(f"Content too large (max {MAX_FILE_SIZE_BYTES} bytes).")

        file_path.write_bytes(data)
        return _ok(message=f"File updated: {path}", bytes=len(data))
    except PathEscapeError as e:
        return _err(str(e))
    except Exception as e:
        return _err(str(e))


def copy_file(source: str, destination: str) -> dict[str, Any]:
    """Copy a file to a new location inside the workspace."""
    try:
        src = safe_path(source)
        dst = safe_path(destination)
        if not src.exists():
            return _err(f"Source not found: {source}")
        if not src.is_file():
            return _err("Only regular files can be copied with this tool.")

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return _ok(message=f"Copied '{source}' → '{destination}'")
    except PathEscapeError as e:
        return _err(str(e))
    except Exception as e:
        return _err(str(e))


def move_file(source: str, destination: str) -> dict[str, Any]:
    """Move or rename a file/folder inside the workspace."""
    try:
        src = safe_path(source)
        dst = safe_path(destination)
        if not src.exists():
            return _err(f"Source not found: {source}")

        if src == WORKSPACE:
            return _err("Refusing to move the workspace root.")

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return _ok(message=f"Moved '{source}' → '{destination}'")
    except PathEscapeError as e:
        return _err(str(e))
    except Exception as e:
        return _err(str(e))


def delete_path(path: str) -> dict[str, Any]:
    """Delete a file or folder (recursive for directories)."""
    try:
        target = safe_path(path)
        if not target.exists():
            return _err(f"Path not found: {path}")

        if target == WORKSPACE:
            return _err("Refusing to delete the workspace root.")

        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        return _ok(message=f"Deleted: {path}")
    except PathEscapeError as e:
        return _err(str(e))
    except Exception as e:
        return _err(str(e))

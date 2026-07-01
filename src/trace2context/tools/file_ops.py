from __future__ import annotations

from pathlib import Path


def safe_workspace_path(workspace: Path | str, path: Path | str) -> Path:
    root = Path(workspace).resolve()
    target = (root / Path(path)).resolve()
    if not target.is_relative_to(root):
        raise ValueError(f"Path escapes workspace: {path}")
    return target


def read_file(path: Path | str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_file(path: Path | str, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def read_workspace_file(workspace: Path | str, path: Path | str) -> str:
    return read_file(safe_workspace_path(workspace, path))


def write_workspace_file(workspace: Path | str, path: Path | str, content: str) -> None:
    write_file(safe_workspace_path(workspace, path), content)

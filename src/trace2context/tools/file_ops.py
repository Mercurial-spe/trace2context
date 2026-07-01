from __future__ import annotations

from pathlib import Path


def read_file(path: Path | str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_file(path: Path | str, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

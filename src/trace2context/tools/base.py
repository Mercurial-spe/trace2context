from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolExecution:
    name: str
    input: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0

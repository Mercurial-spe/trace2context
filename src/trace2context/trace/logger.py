from __future__ import annotations

import json
from pathlib import Path

from trace2context.trace.schema import TraceEvent


class TraceLogger:
    """Append-only JSONL trace logger."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: TraceEvent) -> None:
        with self.path.open("a", encoding="utf-8") as file:
            file.write(event.model_dump_json() + "\n")


def read_trace(path: Path | str) -> list[TraceEvent]:
    trace_path = Path(path)
    events: list[TraceEvent] = []
    if not trace_path.exists():
        raise FileNotFoundError(trace_path)

    with trace_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                events.append(TraceEvent.model_validate_json(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {trace_path}") from exc
    return events

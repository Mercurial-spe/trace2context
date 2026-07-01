from __future__ import annotations

import subprocess
import time
from pathlib import Path

from trace2context.tools.base import ToolExecution


def run_shell(
    command: str,
    cwd: Path | str | None = None,
    timeout_seconds: int = 30,
) -> ToolExecution:
    start = time.perf_counter()
    completed = subprocess.run(
        f"set -o pipefail; {command}",
        cwd=cwd,
        shell=True,
        executable="/bin/bash",
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    duration_ms = int((time.perf_counter() - start) * 1000)
    return ToolExecution(
        name="shell",
        input=command,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_ms=duration_ms,
    )

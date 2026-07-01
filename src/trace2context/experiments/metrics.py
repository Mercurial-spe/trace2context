from __future__ import annotations

from pydantic import BaseModel


class ExperimentMetrics(BaseModel):
    strategy: str
    task_success: bool | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    failed_tool_calls: int = 0
    repeated_errors: int = 0
    long_output_tokens: int = 0

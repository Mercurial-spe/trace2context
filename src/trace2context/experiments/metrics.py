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


class ContextStrategyMetrics(BaseModel):
    strategy: str
    before_tokens: int
    after_tokens: int
    kept_segments: int = 0
    compressed_segments: int = 0
    dropped_segments: int = 0
    notes: str = ""

    @property
    def reduction_ratio(self) -> float:
        if self.before_tokens == 0:
            return 0.0
        return 1 - (self.after_tokens / self.before_tokens)

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(StrEnum):
    MESSAGE = "message"
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    CONTEXT_DECISION = "context_decision"
    ERROR = "error"


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class ContextItemKind(StrEnum):
    SYSTEM_RULES = "system_rules"
    PROJECT_RULES = "project_rules"
    USER_TASK = "user_task"
    ASSISTANT_MESSAGE = "assistant_message"
    TOOL_OUTPUT = "tool_output"
    ERROR = "error"
    FILE_CONTENT = "file_content"
    SUMMARY = "summary"
    TRACE_EVENT = "trace_event"


class ContextAction(StrEnum):
    KEEP = "keep"
    COMPRESS = "compress"
    DROP = "drop"


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    by_source: dict[str, int] = Field(default_factory=dict)


class TraceEvent(BaseModel):
    run_id: str
    step_id: int
    event_type: EventType
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    role: Role | None = None
    content: str = ""
    tool_name: str | None = None
    tool_input: str | dict[str, Any] | None = None
    status: ToolStatus | None = None
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: int | None = None
    files_touched: list[str] = Field(default_factory=list)
    token_count: int = 0
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    audit_tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def output_text(self) -> str:
        return "\n".join(part for part in [self.content, self.stdout, self.stderr] if part)

    def with_tag(self, tag: str) -> TraceEvent:
        if tag not in self.audit_tags:
            self.audit_tags.append(tag)
        return self


class ContextSegment(BaseModel):
    segment_id: str = Field(default_factory=lambda: str(uuid4()))
    source_event_id: str | None = None
    source_step_id: int | None = None
    kind: ContextItemKind
    content: str
    token_count: int = 0
    audit_tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextDecision(BaseModel):
    segment_id: str
    action: ContextAction
    reason: str
    original_tokens: int
    resulting_tokens: int
    priority: int = 0
    summary: str | None = None


class FilterResult(BaseModel):
    before_tokens: int
    after_tokens: int
    decisions: list[ContextDecision]

    @property
    def reduction_ratio(self) -> float:
        if self.before_tokens == 0:
            return 0.0
        return 1 - (self.after_tokens / self.before_tokens)

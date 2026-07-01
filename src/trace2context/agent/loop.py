from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from trace2context.agent.model import ChatResponse
from trace2context.agent.parser import ActionParseError, AgentAction, parse_action
from trace2context.agent.prompts import DEFAULT_SYSTEM_PROMPT
from trace2context.audit.analyzer import AuditAnalyzer
from trace2context.context.builder import segments_from_events
from trace2context.context.filter import AuditAwareFilter
from trace2context.reporting.markdown import render_audit_report
from trace2context.tools.file_ops import read_workspace_file, write_workspace_file
from trace2context.tools.shell import run_shell
from trace2context.trace.logger import TraceLogger
from trace2context.trace.schema import (
    ContextAction,
    ContextDecision,
    ContextSegment,
    EventType,
    Role,
    TokenUsage,
    ToolStatus,
    TraceEvent,
)
from trace2context.trace.token_counter import count_tokens


class ChatClient(Protocol):
    def chat(self, messages: list[dict[str, str]], max_tokens: int = 1200) -> ChatResponse:
        ...


class AgentRunResult(BaseModel):
    run_id: str
    run_dir: Path
    trace_path: Path
    report_path: Path
    final_answer: str = ""
    steps: int = 0
    success: bool = False


class MinimalCodingAgent:
    """A small coding agent with audit-aware context management."""

    def __init__(
        self,
        model_client: ChatClient,
        workspace: Path | str,
        run_root: Path | str = "runs",
        max_steps: int = 8,
        model_max_tokens: int = 800,
        context_token_budget: int = 6000,
    ) -> None:
        self.model_client = model_client
        self.workspace = Path(workspace).resolve()
        self.run_root = Path(run_root)
        self.max_steps = max_steps
        self.model_max_tokens = model_max_tokens
        self.context_token_budget = context_token_budget

    def run(self, task: str) -> AgentRunResult:
        run_id = datetime.now(UTC).strftime("run_%Y%m%d_%H%M%S_%f")
        run_dir = self.run_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        trace_path = run_dir / "trace.jsonl"
        report_path = run_dir / "audit_report.md"
        logger = TraceLogger(trace_path)
        events: list[TraceEvent] = []
        next_step = 1

        next_step = self._append_event(
            events,
            logger,
            TraceEvent(
                run_id=run_id,
                step_id=next_step,
                event_type=EventType.MESSAGE,
                role=Role.USER,
                content=task,
                token_count=count_tokens(task),
            ),
        )

        final_answer = ""
        success = False
        for _ in range(self.max_steps):
            try:
                response = self.model_client.chat(
                    self._build_messages(task, events),
                    max_tokens=self.model_max_tokens,
                )
            except Exception as exc:
                next_step = self._append_event(
                    events,
                    logger,
                    TraceEvent(
                        run_id=run_id,
                        step_id=next_step,
                        event_type=EventType.ERROR,
                        content=str(exc),
                        token_count=count_tokens(str(exc)),
                        audit_tags=["model_call_error"],
                    ),
                )
                break

            next_step = self._append_event(
                events,
                logger,
                self._assistant_event(run_id, next_step, response),
            )

            try:
                action = parse_action(response.content)
            except ActionParseError as exc:
                next_step = self._append_event(
                    events,
                    logger,
                    TraceEvent(
                        run_id=run_id,
                        step_id=next_step,
                        event_type=EventType.ERROR,
                        content=str(exc),
                        token_count=count_tokens(str(exc)),
                        audit_tags=["invalid_agent_action"],
                    ),
                )
                break

            if action.action == "finish":
                final_answer = str(action.args.get("answer", ""))
                success = True
                break

            next_step = self._append_event(
                events,
                logger,
                self._execute_action(run_id, next_step, action),
            )

        analysis = AuditAnalyzer().analyze(events)
        filter_result = AuditAwareFilter(
            token_budget=self.context_token_budget
        ).filter_events(events)
        report_path.write_text(render_audit_report(analysis, filter_result), encoding="utf-8")
        return AgentRunResult(
            run_id=run_id,
            run_dir=run_dir,
            trace_path=trace_path,
            report_path=report_path,
            final_answer=final_answer,
            steps=next_step - 1,
            success=success,
        )

    def _build_messages(self, task: str, events: list[TraceEvent]) -> list[dict[str, str]]:
        audited_events = [event.model_copy(deep=True) for event in events]
        AuditAnalyzer().analyze(audited_events)
        context = self._render_context(audited_events)
        return [
            {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Workspace: {self.workspace}\n"
                    f"Task: {task}\n\n"
                    f"Trace:\n{context}\n\n"
                    "Select next action as JSON."
                ),
            },
        ]

    def _render_context(self, events: list[TraceEvent]) -> str:
        if not events:
            return "- No prior events."

        segments = segments_from_events(events)
        filter_result = AuditAwareFilter(
            token_budget=self.context_token_budget
        ).filter_segments(segments)
        decision_by_segment_id = {
            decision.segment_id: decision for decision in filter_result.decisions
        }
        rendered = [
            self._render_segment(segment, decision_by_segment_id[segment.segment_id])
            for segment in segments
            if decision_by_segment_id[segment.segment_id].action != ContextAction.DROP
        ]
        if rendered:
            return "\n".join(rendered[-12:])

        # Fall back to event-level rendering if every content segment was dropped.
        lines: list[str] = []
        for event in events[-12:]:
            tags = f" tags={','.join(event.audit_tags)}" if event.audit_tags else ""
            if event.event_type == EventType.MESSAGE:
                lines.append(f"step {event.step_id}: {_shorten(event.content)}{tags}")
            elif event.event_type in {
                EventType.TOOL_RESULT,
                EventType.FILE_READ,
                EventType.FILE_WRITE,
            }:
                status = event.status.value if event.status else "unknown"
                output = _shorten(event.stderr or event.stdout or event.content)
                lines.append(
                    f"step {event.step_id}: tool={event.tool_name} status={status} "
                    f"input={event.tool_input!r} output={output}{tags}"
                )
            else:
                lines.append(
                    f"step {event.step_id}: {event.event_type}: "
                    f"{_shorten(event.content)}{tags}"
                )
        return "\n".join(lines)

    def _render_segment(
        self,
        segment: ContextSegment,
        decision: ContextDecision,
    ) -> str:
        tags = f" tags={','.join(segment.audit_tags)}" if segment.audit_tags else ""
        status = segment.metadata.get("status")
        tool_name = segment.metadata.get("tool_name")
        tool = f" tool={tool_name}" if tool_name else ""
        status_text = f" status={status}" if status else ""
        if decision.action == ContextAction.COMPRESS:
            content = decision.summary or _shorten(segment.content, limit=120)
        else:
            content = _shorten(segment.content)
        return (
            f"step {segment.source_step_id}: {decision.action.value} "
            f"{segment.kind.value}{tool}{status_text}: {content}{tags}"
        )

    def _assistant_event(self, run_id: str, step_id: int, response: ChatResponse) -> TraceEvent:
        usage = response.usage or {}
        return TraceEvent(
            run_id=run_id,
            step_id=step_id,
            event_type=EventType.MESSAGE,
            role=Role.ASSISTANT,
            content=response.content,
            token_count=count_tokens(response.content),
            token_usage=TokenUsage(
                input_tokens=int(usage.get("prompt_tokens") or 0),
                output_tokens=int(usage.get("completion_tokens") or 0),
                total_tokens=int(usage.get("total_tokens") or 0),
            ),
            metadata={"model_usage": usage},
        )

    def _execute_action(self, run_id: str, step_id: int, action: AgentAction) -> TraceEvent:
        try:
            if action.action == "read_file":
                path = str(action.args["path"])
                content = read_workspace_file(self.workspace, path)
                return TraceEvent(
                    run_id=run_id,
                    step_id=step_id,
                    event_type=EventType.FILE_READ,
                    tool_name="read_file",
                    tool_input=path,
                    status=ToolStatus.SUCCESS,
                    stdout=content,
                    files_touched=[path],
                    token_count=count_tokens(content),
                )

            if action.action == "write_file":
                path = str(action.args["path"])
                content = str(action.args["content"])
                write_workspace_file(self.workspace, path, content)
                return TraceEvent(
                    run_id=run_id,
                    step_id=step_id,
                    event_type=EventType.FILE_WRITE,
                    tool_name="write_file",
                    tool_input=path,
                    status=ToolStatus.SUCCESS,
                    content=f"Wrote {path}",
                    files_touched=[path],
                    token_count=count_tokens(content),
                )

            if action.action == "shell":
                command = str(action.args["command"])
                execution = run_shell(command, cwd=self.workspace, timeout_seconds=60)
                status = ToolStatus.SUCCESS if execution.succeeded else ToolStatus.FAILED
                output = execution.stdout + execution.stderr
                return TraceEvent(
                    run_id=run_id,
                    step_id=step_id,
                    event_type=EventType.TOOL_RESULT,
                    tool_name="shell",
                    tool_input=command,
                    status=status,
                    exit_code=execution.exit_code,
                    stdout=execution.stdout,
                    stderr=execution.stderr,
                    duration_ms=execution.duration_ms,
                    token_count=count_tokens(output),
                )
        except Exception as exc:
            return TraceEvent(
                run_id=run_id,
                step_id=step_id,
                event_type=EventType.ERROR,
                tool_name=action.action,
                tool_input=action.args,
                status=ToolStatus.FAILED,
                content=str(exc),
                token_count=count_tokens(str(exc)),
                audit_tags=["tool_wrapper_error"],
            )

        raise ValueError(f"Unsupported action: {action.action}")

    def _append_event(
        self,
        events: list[TraceEvent],
        logger: TraceLogger,
        event: TraceEvent,
    ) -> int:
        events.append(event)
        logger.append(event)
        return event.step_id + 1


def _shorten(text: str, limit: int = 260) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    head_len = max(1, limit // 2 - 3)
    tail_len = max(1, limit - head_len - 5)
    return f"{compact[:head_len]} ... {compact[-tail_len:]}"

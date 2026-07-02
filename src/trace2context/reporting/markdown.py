from __future__ import annotations

from collections import Counter

from trace2context.audit import rules
from trace2context.audit.analyzer import AuditAnalysis
from trace2context.trace.schema import (
    ContextAction,
    EventType,
    FilterResult,
    ToolStatus,
    TraceEvent,
)

FAILURE_TAGS = {
    rules.FAILED_TOOL_CALL,
    rules.FAILED_TEST_COMMAND,
    "model_call_error",
    "tool_wrapper_error",
    "invalid_agent_action",
}


def render_audit_report(analysis: AuditAnalysis, filter_result: FilterResult) -> str:
    lines = [
        "# Trace2Context Audit Report",
        "",
        "## Run Summary",
        "",
        f"- Total events: {len(analysis.events)}",
        f"- Tool results: {analysis.tool_call_count}",
        f"- Estimated trace tokens: {analysis.total_tokens}",
        f"- Context tokens before filtering: {filter_result.before_tokens}",
        f"- Context tokens after filtering: {filter_result.after_tokens}",
        f"- Estimated reduction: {filter_result.reduction_ratio:.1%}",
        "",
        "## Context Decision Summary",
        "",
    ]

    lines.extend(_context_decision_summary(filter_result))
    lines.extend(["", "## Top Token Burners", ""])
    lines.extend(_top_token_burners(analysis.events))
    lines.extend(["", "## Failure Timeline", ""])
    lines.extend(_failure_timeline(analysis.events))
    lines.extend(["", "## Audit Tags", ""])

    if analysis.tag_counts:
        for tag, count in analysis.tag_counts.most_common():
            lines.append(f"- `{tag}`: {count}")
    else:
        lines.append("- No audit tags detected.")

    lines.extend(["", "## Context Decisions", ""])
    for action in ContextAction:
        grouped = [decision for decision in filter_result.decisions if decision.action == action]
        lines.extend([f"### {action.value.title()}", ""])
        if not grouped:
            lines.append("- None")
            lines.append("")
            continue
        for decision in grouped:
            lines.append(
                f"- `{decision.segment_id}`: {decision.reason} "
                f"({decision.original_tokens} -> {decision.resulting_tokens} tokens)"
            )
            if decision.summary:
                lines.append(f"  Summary: {decision.summary}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _context_decision_summary(filter_result: FilterResult) -> list[str]:
    counts: Counter[ContextAction] = Counter()
    original_tokens: Counter[ContextAction] = Counter()
    resulting_tokens: Counter[ContextAction] = Counter()

    for decision in filter_result.decisions:
        counts[decision.action] += 1
        original_tokens[decision.action] += decision.original_tokens
        resulting_tokens[decision.action] += decision.resulting_tokens

    lines = [
        "| Action | Segments | Original tokens | Result tokens | Delta |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for action in ContextAction:
        original = original_tokens[action]
        resulting = resulting_tokens[action]
        lines.append(
            f"| `{action.value}` | {counts[action]} | {original} | {resulting} | "
            f"{resulting - original} |"
        )

    token_delta = filter_result.after_tokens - filter_result.before_tokens
    lines.append(
        f"| **total** | {len(filter_result.decisions)} | {filter_result.before_tokens} | "
        f"{filter_result.after_tokens} | {token_delta} |"
    )
    return lines


def _top_token_burners(events: list[TraceEvent], limit: int = 5) -> list[str]:
    ranked_events = sorted(
        (event for event in events if event.token_count > 0),
        key=lambda event: event.token_count,
        reverse=True,
    )[:limit]

    if not ranked_events:
        return ["- No event token counts recorded."]

    lines: list[str] = []
    for event in ranked_events:
        line = f"- {_event_label(event)}: {event.token_count} tokens"
        if event.audit_tags:
            line += f"; tags: {_format_tags(event.audit_tags)}"
        preview = _preview_output(event)
        if preview:
            line += f"; preview: {preview}"
        lines.append(line)
    return lines


def _failure_timeline(events: list[TraceEvent]) -> list[str]:
    failures = [
        event for event in sorted(events, key=lambda item: item.step_id) if _is_failure(event)
    ]
    if not failures:
        return ["- No failures detected."]

    lines: list[str] = []
    for event in failures:
        line = f"- {_event_label(event)}"
        details = []
        if event.status:
            details.append(f"status={event.status.value}")
        if event.exit_code is not None:
            details.append(f"exit_code={event.exit_code}")
        if event.audit_tags:
            details.append(f"tags={_format_tags(event.audit_tags)}")
        if details:
            line += f" ({'; '.join(details)})"
        preview = _preview_output(event)
        if preview:
            line += f": {preview}"
        lines.append(line)
    return lines


def _is_failure(event: TraceEvent) -> bool:
    return (
        event.event_type == EventType.ERROR
        or event.status == ToolStatus.FAILED
        or bool(FAILURE_TAGS.intersection(event.audit_tags))
    )


def _event_label(event: TraceEvent) -> str:
    parts = [f"Step {event.step_id}", _inline_code(event.event_type.value)]
    if event.tool_name:
        parts.append(event.tool_name)
    if event.tool_input:
        parts.append(_inline_code(_format_tool_input(event.tool_input)))
    return " ".join(parts)


def _format_tool_input(tool_input: object) -> str:
    if isinstance(tool_input, dict):
        if "command" in tool_input:
            return str(tool_input["command"])
        if "path" in tool_input:
            return str(tool_input["path"])
    return str(tool_input)


def _preview_output(event: TraceEvent, limit: int = 180) -> str:
    compact = " ".join(event.output_text.split())
    if not compact:
        return ""
    if len(compact) > limit:
        compact = compact[: limit - 3].rstrip() + "..."
    return _inline_code(compact)


def _format_tags(tags: list[str]) -> str:
    return ", ".join(_inline_code(tag) for tag in tags)


def _inline_code(text: str) -> str:
    escaped = text.replace("`", "'")
    return f"`{escaped}`"

from __future__ import annotations

from trace2context.trace.schema import ContextItemKind, ContextSegment, EventType, Role, TraceEvent


def segments_from_events(events: list[TraceEvent]) -> list[ContextSegment]:
    segments: list[ContextSegment] = []
    for event in events:
        content = event.output_text
        if not content:
            continue
        segments.append(
            ContextSegment(
                source_event_id=event.event_id,
                source_step_id=event.step_id,
                kind=_kind_for_event(event),
                content=content,
                token_count=event.token_count,
                audit_tags=list(event.audit_tags),
                metadata={
                    "event_type": event.event_type.value,
                    "tool_name": event.tool_name,
                    "status": event.status.value if event.status else None,
                },
            )
        )
    return segments


def _kind_for_event(event: TraceEvent) -> ContextItemKind:
    if event.role == Role.USER:
        return ContextItemKind.USER_TASK
    if event.role == Role.ASSISTANT:
        return ContextItemKind.ASSISTANT_MESSAGE
    if event.event_type == EventType.FILE_READ:
        return ContextItemKind.FILE_CONTENT
    if event.event_type == EventType.TOOL_RESULT:
        return ContextItemKind.TOOL_OUTPUT
    if event.event_type == EventType.ERROR:
        return ContextItemKind.ERROR
    return ContextItemKind.TRACE_EVENT

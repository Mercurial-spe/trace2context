from __future__ import annotations

from pathlib import Path

from trace2context.audit.analyzer import AuditAnalyzer
from trace2context.context.builder import segments_from_events
from trace2context.context.filter import AuditAwareFilter
from trace2context.experiments.metrics import ContextStrategyMetrics
from trace2context.reporting.markdown import render_audit_report
from trace2context.trace.logger import read_trace
from trace2context.trace.schema import ContextAction, TraceEvent


def analyze_trace_file(trace_path: Path, report_path: Path) -> None:
    events = read_trace(trace_path)
    analysis = AuditAnalyzer().analyze(events)
    filter_result = AuditAwareFilter().filter_events(events)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_audit_report(analysis, filter_result), encoding="utf-8")


def compare_context_strategies(
    events: list[TraceEvent],
    recent_n: int = 6,
    token_budget: int | None = None,
) -> list[ContextStrategyMetrics]:
    audited_events = [event.model_copy(deep=True) for event in events]
    AuditAnalyzer().analyze(audited_events)
    segments = segments_from_events(audited_events)
    before_tokens = sum(segment.token_count for segment in segments)

    recent_segments = segments[-recent_n:] if recent_n > 0 else []
    recent_tokens = sum(segment.token_count for segment in recent_segments)

    audit_filter = AuditAwareFilter(token_budget=token_budget)
    audit_result = audit_filter.filter_segments(segments)
    action_counts = {action: 0 for action in ContextAction}
    for decision in audit_result.decisions:
        action_counts[decision.action] += 1

    return [
        ContextStrategyMetrics(
            strategy="full_history",
            before_tokens=before_tokens,
            after_tokens=before_tokens,
            kept_segments=len(segments),
            notes="all context segments are kept",
        ),
        ContextStrategyMetrics(
            strategy=f"recent_{recent_n}",
            before_tokens=before_tokens,
            after_tokens=recent_tokens,
            kept_segments=len(recent_segments),
            dropped_segments=max(0, len(segments) - len(recent_segments)),
            notes=f"only the most recent {recent_n} context segments are kept",
        ),
        ContextStrategyMetrics(
            strategy="audit_aware",
            before_tokens=audit_result.before_tokens,
            after_tokens=audit_result.after_tokens,
            kept_segments=action_counts[ContextAction.KEEP],
            compressed_segments=action_counts[ContextAction.COMPRESS],
            dropped_segments=action_counts[ContextAction.DROP],
            notes="audit tags drive keep/compress/drop decisions",
        ),
    ]

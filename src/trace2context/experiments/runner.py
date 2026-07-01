from __future__ import annotations

from pathlib import Path

from trace2context.audit.analyzer import AuditAnalyzer
from trace2context.context.filter import AuditAwareFilter
from trace2context.reporting.markdown import render_audit_report
from trace2context.trace.logger import read_trace


def analyze_trace_file(trace_path: Path, report_path: Path) -> None:
    events = read_trace(trace_path)
    analysis = AuditAnalyzer().analyze(events)
    filter_result = AuditAwareFilter().filter_events(events)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_audit_report(analysis, filter_result), encoding="utf-8")

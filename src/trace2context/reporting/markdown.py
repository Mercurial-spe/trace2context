from __future__ import annotations

from trace2context.audit.analyzer import AuditAnalysis
from trace2context.trace.schema import ContextAction, FilterResult


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
        "## Audit Tags",
        "",
    ]

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

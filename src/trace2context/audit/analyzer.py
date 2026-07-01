from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from rich.table import Table

from trace2context.audit import rules
from trace2context.trace.schema import EventType, TraceEvent


@dataclass
class AuditAnalysis:
    events: list[TraceEvent]

    @property
    def tag_counts(self) -> Counter[str]:
        counts: Counter[str] = Counter()
        for event in self.events:
            counts.update(event.audit_tags)
        return counts

    @property
    def total_tokens(self) -> int:
        return sum(event.token_count for event in self.events)

    @property
    def tool_call_count(self) -> int:
        return sum(1 for event in self.events if event.event_type == EventType.TOOL_RESULT)

    def to_table(self) -> Table:
        table = Table(title="Trace2Context Audit Summary")
        table.add_column("Metric")
        table.add_column("Value", justify="right")
        table.add_row("events", str(len(self.events)))
        table.add_row("tool_results", str(self.tool_call_count))
        table.add_row("estimated_tokens", str(self.total_tokens))
        for tag, count in self.tag_counts.most_common():
            table.add_row(tag, str(count))
        return table


class AuditAnalyzer:
    def __init__(self, long_output_threshold_tokens: int = 800) -> None:
        self.long_output_threshold_tokens = long_output_threshold_tokens

    def analyze(self, events: list[TraceEvent]) -> AuditAnalysis:
        for event in events:
            rules.tag_failed_tool_call(event)
            rules.tag_long_tool_output(event, self.long_output_threshold_tokens)
            rules.tag_successful_test_command(event)
            rules.tag_modified_file(event)
            rules.tag_possible_tool_hallucination(event)

        rules.tag_repeated_commands(events)
        rules.tag_repeated_errors(events)
        return AuditAnalysis(events=events)

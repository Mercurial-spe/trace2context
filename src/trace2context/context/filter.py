from __future__ import annotations

from trace2context.audit import rules
from trace2context.context.builder import segments_from_events
from trace2context.context.decisions import COMPRESS_REASONS, DEFAULT_PRIORITY, KEEP_REASONS
from trace2context.trace.schema import (
    ContextAction,
    ContextDecision,
    ContextItemKind,
    ContextSegment,
    FilterResult,
    TraceEvent,
)


class AuditAwareFilter:
    """Simple audit-aware filtering policy.

    The policy keeps root objectives and high-value evidence, compresses repeated
    or long outputs, and drops old low-value outputs only when a budget is set.
    """

    def __init__(self, token_budget: int | None = None, compression_ratio: float = 0.2) -> None:
        self.token_budget = token_budget
        self.compression_ratio = compression_ratio

    def filter_events(self, events: list[TraceEvent]) -> FilterResult:
        return self.filter_segments(segments_from_events(events))

    def filter_segments(self, segments: list[ContextSegment]) -> FilterResult:
        decisions = [self._decide(segment) for segment in segments]
        if self.token_budget is not None:
            decisions = self._apply_budget(decisions)
        before_tokens = sum(decision.original_tokens for decision in decisions)
        after_tokens = sum(decision.resulting_tokens for decision in decisions)
        return FilterResult(
            before_tokens=before_tokens,
            after_tokens=after_tokens,
            decisions=decisions,
        )

    def _decide(self, segment: ContextSegment) -> ContextDecision:
        tags = set(segment.audit_tags)
        if segment.kind == ContextItemKind.USER_TASK:
            return self._decision(segment, ContextAction.KEEP, KEEP_REASONS["root_task"])
        if rules.SUCCESSFUL_TEST_COMMAND in tags:
            return self._decision(segment, ContextAction.KEEP, KEEP_REASONS["successful_test"])
        if rules.MODIFIED_FILE in tags:
            return self._decision(segment, ContextAction.KEEP, KEEP_REASONS["modified_file"])
        if rules.REPEATED_ERROR in tags or rules.LONG_TOOL_OUTPUT in tags:
            reason = (
                COMPRESS_REASONS["repeated_error"]
                if rules.REPEATED_ERROR in tags
                else COMPRESS_REASONS["long_output"]
            )
            return self._decision(segment, ContextAction.COMPRESS, reason)
        if rules.FAILED_TEST_COMMAND in tags:
            return self._decision(segment, ContextAction.KEEP, KEEP_REASONS["failed_test"])
        if rules.FAILED_TOOL_CALL in tags:
            return self._decision(segment, ContextAction.KEEP, KEEP_REASONS["latest_error"])
        return self._decision(segment, ContextAction.KEEP, "default retention")

    def _decision(
        self, segment: ContextSegment, action: ContextAction, reason: str
    ) -> ContextDecision:
        resulting_tokens = segment.token_count
        summary = None
        if action == ContextAction.COMPRESS:
            resulting_tokens = max(1, int(segment.token_count * self.compression_ratio))
            summary = _summarize(segment)
        elif action == ContextAction.DROP:
            resulting_tokens = 0

        return ContextDecision(
            segment_id=segment.segment_id,
            action=action,
            reason=reason,
            original_tokens=segment.token_count,
            resulting_tokens=resulting_tokens,
            priority=DEFAULT_PRIORITY[action],
            summary=summary,
        )

    def _apply_budget(self, decisions: list[ContextDecision]) -> list[ContextDecision]:
        current = sum(decision.resulting_tokens for decision in decisions)
        if current <= self.token_budget:
            return decisions

        adjusted = list(decisions)
        for decision in sorted(adjusted, key=lambda item: (item.priority, item.original_tokens)):
            if current <= self.token_budget:
                break
            if decision.action == ContextAction.KEEP and decision.reason == "default retention":
                current -= decision.resulting_tokens
                decision.action = ContextAction.DROP
                decision.resulting_tokens = 0
                decision.reason = "over token budget and no audit evidence"
        return adjusted


def _summarize(segment: ContextSegment) -> str:
    first_line = next((line.strip() for line in segment.content.splitlines() if line.strip()), "")
    if len(first_line) > 160:
        first_line = first_line[:157] + "..."
    return first_line

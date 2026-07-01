from trace2context.experiments.runner import compare_context_strategies
from trace2context.trace.schema import EventType, Role, ToolStatus, TraceEvent


def test_compare_context_strategies_reports_baselines_and_audit_aware():
    events = [
        TraceEvent(
            run_id="run_test",
            step_id=1,
            event_type=EventType.MESSAGE,
            role=Role.USER,
            content="Fix failing test.",
            token_count=4,
        ),
        TraceEvent(
            run_id="run_test",
            step_id=2,
            event_type=EventType.TOOL_RESULT,
            tool_name="shell",
            tool_input="pytest",
            status=ToolStatus.FAILED,
            exit_code=1,
            stdout="first line\n" + ("noise " * 1200),
            token_count=1000,
        ),
    ]

    metrics = compare_context_strategies(events, recent_n=1)
    by_strategy = {item.strategy: item for item in metrics}

    assert by_strategy["full_history"].after_tokens == 1004
    assert by_strategy["recent_1"].after_tokens == 1000
    assert by_strategy["audit_aware"].compressed_segments == 1
    assert by_strategy["audit_aware"].after_tokens < by_strategy["full_history"].after_tokens

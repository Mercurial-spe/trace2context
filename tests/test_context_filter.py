from trace2context.audit.analyzer import AuditAnalyzer
from trace2context.context.filter import AuditAwareFilter
from trace2context.trace.schema import ContextAction, EventType, Role, ToolStatus, TraceEvent


def test_audit_filter_compresses_repeated_error_and_keeps_user_task():
    events = [
        TraceEvent(
            run_id="run_test",
            step_id=1,
            event_type=EventType.MESSAGE,
            role=Role.USER,
            content="Fix the calculator bug.",
            token_count=5,
        ),
        TraceEvent(
            run_id="run_test",
            step_id=2,
            event_type=EventType.TOOL_RESULT,
            tool_name="shell",
            tool_input="pytest",
            status=ToolStatus.FAILED,
            exit_code=1,
            stderr="AssertionError: expected 4 got 5",
            token_count=100,
        ),
        TraceEvent(
            run_id="run_test",
            step_id=3,
            event_type=EventType.TOOL_RESULT,
            tool_name="shell",
            tool_input="pytest",
            status=ToolStatus.FAILED,
            exit_code=1,
            stderr="AssertionError: expected 4 got 9",
            token_count=100,
        ),
    ]
    AuditAnalyzer(long_output_threshold_tokens=1000).analyze(events)

    result = AuditAwareFilter().filter_events(events)

    assert result.before_tokens == 205
    assert result.after_tokens < result.before_tokens
    assert any(decision.action == ContextAction.KEEP for decision in result.decisions)
    assert any(decision.action == ContextAction.COMPRESS for decision in result.decisions)


def test_audit_filter_keeps_masked_failed_test_output_under_budget():
    events = [
        TraceEvent(
            run_id="run_test",
            step_id=1,
            event_type=EventType.TOOL_RESULT,
            tool_name="shell",
            tool_input="python -m pytest --tb=short 2>&1 | head -100",
            status=ToolStatus.SUCCESS,
            exit_code=0,
            stdout="FAILED tests/test_calc.py::test_add - assert 5 == 4",
            token_count=100,
        ),
        TraceEvent(
            run_id="run_test",
            step_id=2,
            event_type=EventType.MESSAGE,
            role=Role.ASSISTANT,
            content="Some low-value intermediate thought.",
            token_count=100,
        ),
    ]
    AuditAnalyzer(long_output_threshold_tokens=1000).analyze(events)

    result = AuditAwareFilter(token_budget=50).filter_events(events)

    failed_test_decisions = [
        decision for decision in result.decisions if decision.reason == "failed test evidence"
    ]
    assert failed_test_decisions
    assert failed_test_decisions[0].action == ContextAction.KEEP
    assert any(decision.action == ContextAction.DROP for decision in result.decisions)

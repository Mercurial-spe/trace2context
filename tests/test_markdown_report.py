from trace2context.audit.analyzer import AuditAnalyzer
from trace2context.reporting.markdown import render_audit_report
from trace2context.trace.schema import (
    ContextAction,
    ContextDecision,
    EventType,
    FilterResult,
    Role,
    ToolStatus,
    TraceEvent,
)


def test_render_audit_report_includes_context_and_failure_summaries():
    events = [
        TraceEvent(
            run_id="run_test",
            step_id=1,
            event_type=EventType.MESSAGE,
            role=Role.USER,
            content="Fix failing test.",
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
            stdout="FAILED tests/test_calc.py::test_add - assert 5 == 4\n" + ("noise " * 100),
            token_count=1000,
        ),
        TraceEvent(
            run_id="run_test",
            step_id=3,
            event_type=EventType.ERROR,
            tool_name="model",
            status=ToolStatus.FAILED,
            content="Chat completion failed with HTTP 504",
            token_count=7,
            audit_tags=["model_call_error"],
        ),
    ]
    analysis = AuditAnalyzer(long_output_threshold_tokens=800).analyze(events)
    filter_result = FilterResult(
        before_tokens=1055,
        after_tokens=205,
        decisions=[
            ContextDecision(
                segment_id="task",
                action=ContextAction.KEEP,
                reason="root user task",
                original_tokens=5,
                resulting_tokens=5,
            ),
            ContextDecision(
                segment_id="failed-output",
                action=ContextAction.COMPRESS,
                reason="long tool output",
                original_tokens=1000,
                resulting_tokens=200,
                summary="FAILED tests/test_calc.py::test_add",
            ),
            ContextDecision(
                segment_id="old-output",
                action=ContextAction.DROP,
                reason="over token budget and no audit evidence",
                original_tokens=50,
                resulting_tokens=0,
            ),
        ],
    )

    report = render_audit_report(analysis, filter_result)

    assert "## Context Decision Summary" in report
    assert "| `keep` | 1 | 5 | 5 | 0 |" in report
    assert "| `compress` | 1 | 1000 | 200 | -800 |" in report
    assert "| `drop` | 1 | 50 | 0 | -50 |" in report
    assert "| **total** | 3 | 1055 | 205 | -850 |" in report
    assert "## Top Token Burners" in report
    assert "Step 2 `tool_result` shell `pytest`: 1000 tokens" in report
    assert "## Failure Timeline" in report
    assert "status=failed; exit_code=1" in report
    assert "`failed_test_command`" in report
    assert "Chat completion failed with HTTP 504" in report

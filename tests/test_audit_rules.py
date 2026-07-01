from trace2context.audit.analyzer import AuditAnalyzer
from trace2context.audit.rules import (
    FAILED_TOOL_CALL,
    POSSIBLE_TOOL_HALLUCINATION,
    REPEATED_COMMAND,
    REPEATED_ERROR,
)
from trace2context.trace.schema import EventType, Role, ToolStatus, TraceEvent


def test_analyzer_tags_repeated_failed_command_and_error():
    events = [
        TraceEvent(
            run_id="run_test",
            step_id=1,
            event_type=EventType.TOOL_RESULT,
            tool_name="shell",
            tool_input="pytest tests/test_calc.py",
            status=ToolStatus.FAILED,
            exit_code=1,
            stderr="AssertionError: expected 4 got 5",
            token_count=20,
        ),
        TraceEvent(
            run_id="run_test",
            step_id=2,
            event_type=EventType.TOOL_RESULT,
            tool_name="shell",
            tool_input="pytest tests/test_calc.py",
            status=ToolStatus.FAILED,
            exit_code=1,
            stderr="AssertionError: expected 4 got 9",
            token_count=20,
        ),
    ]

    analysis = AuditAnalyzer(long_output_threshold_tokens=1000).analyze(events)

    assert analysis.tag_counts[FAILED_TOOL_CALL] == 2
    assert analysis.tag_counts[REPEATED_COMMAND] == 2
    assert analysis.tag_counts[REPEATED_ERROR] == 2


def test_analyzer_tags_possible_tool_hallucination():
    events = [
        TraceEvent(
            run_id="run_test",
            step_id=1,
            event_type=EventType.MESSAGE,
            role=Role.ASSISTANT,
            content='I will use {"tool": "shell", "args": "pytest"} now.',
            token_count=12,
        )
    ]

    analysis = AuditAnalyzer().analyze(events)

    assert analysis.tag_counts[POSSIBLE_TOOL_HALLUCINATION] == 1

from trace2context.audit.analyzer import AuditAnalyzer
from trace2context.audit.rules import (
    FAILED_TEST_COMMAND,
    FAILED_TOOL_CALL,
    MODIFIED_FILE,
    PIPELINE_COMMAND,
    POSSIBLE_TOOL_HALLUCINATION,
    REPEATED_COMMAND,
    REPEATED_ERROR,
    SUCCESSFUL_TEST_COMMAND,
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
    assert analysis.tag_counts[FAILED_TEST_COMMAND] == 2
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


def test_analyzer_tags_pipeline_command():
    events = [
        TraceEvent(
            run_id="run_test",
            step_id=1,
            event_type=EventType.TOOL_RESULT,
            tool_name="shell",
            tool_input="python -m pytest --tb=short | head -100",
            status=ToolStatus.FAILED,
            exit_code=1,
            stdout="FAILED tests/test_calc.py::test_add",
            token_count=20,
        )
    ]

    analysis = AuditAnalyzer().analyze(events)

    assert analysis.tag_counts[PIPELINE_COMMAND] == 1
    assert analysis.tag_counts[FAILED_TEST_COMMAND] == 1
    assert analysis.tag_counts[SUCCESSFUL_TEST_COMMAND] == 0


def test_analyzer_detects_failed_test_output_when_pipeline_masks_exit_code():
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
            token_count=20,
        )
    ]

    analysis = AuditAnalyzer().analyze(events)

    assert analysis.tag_counts[PIPELINE_COMMAND] == 1
    assert analysis.tag_counts[FAILED_TEST_COMMAND] == 1


def test_analyzer_tags_file_write_but_not_file_read_as_modified():
    events = [
        TraceEvent(
            run_id="run_test",
            step_id=1,
            event_type=EventType.FILE_READ,
            tool_name="read_file",
            tool_input="src/calc.py",
            files_touched=["src/calc.py"],
            token_count=10,
        ),
        TraceEvent(
            run_id="run_test",
            step_id=2,
            event_type=EventType.FILE_WRITE,
            tool_name="write_file",
            tool_input="src/calc.py",
            files_touched=["src/calc.py"],
            token_count=10,
        ),
    ]

    analysis = AuditAnalyzer().analyze(events)

    assert MODIFIED_FILE not in events[0].audit_tags
    assert MODIFIED_FILE in events[1].audit_tags
    assert analysis.tag_counts[MODIFIED_FILE] == 1

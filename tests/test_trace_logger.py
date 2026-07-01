from trace2context.trace.logger import TraceLogger, read_trace
from trace2context.trace.schema import EventType, Role, TraceEvent


def test_trace_logger_round_trip(tmp_path):
    trace_path = tmp_path / "trace.jsonl"
    event = TraceEvent(
        run_id="run_test",
        step_id=1,
        event_type=EventType.MESSAGE,
        role=Role.USER,
        content="Fix the failing test.",
        token_count=5,
    )

    TraceLogger(trace_path).append(event)
    loaded = read_trace(trace_path)

    assert len(loaded) == 1
    assert loaded[0].run_id == "run_test"
    assert loaded[0].content == "Fix the failing test."

from pathlib import Path

from trace2context.audit.analyzer import AuditAnalyzer
from trace2context.audit.rules import FAILED_TEST_COMMAND, PIPELINE_COMMAND, SUCCESSFUL_TEST_COMMAND
from trace2context.trace.logger import read_trace

TRACE_DIR = Path("examples/simulated_traces")


def test_simulated_trace_fixtures_parse_and_analyze():
    for trace_path in TRACE_DIR.glob("*.jsonl"):
        events = read_trace(trace_path)
        analysis = AuditAnalyzer().analyze(events)

        assert events, f"{trace_path} should contain at least one event"
        assert analysis.total_tokens > 0


def test_pipeline_masked_failure_fixture_exercises_audit_tags():
    events = read_trace(TRACE_DIR / "pipeline_masked_failure.jsonl")
    analysis = AuditAnalyzer().analyze(events)

    assert analysis.tag_counts[PIPELINE_COMMAND] == 1
    assert analysis.tag_counts[FAILED_TEST_COMMAND] == 1
    assert analysis.tag_counts[SUCCESSFUL_TEST_COMMAND] == 1

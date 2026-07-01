from trace2context.agent.loop import MinimalCodingAgent
from trace2context.agent.model import ChatResponse
from trace2context.trace.logger import read_trace
from trace2context.trace.schema import EventType


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)

    def chat(self, messages, max_tokens=1200):
        del messages, max_tokens
        return ChatResponse(content=self.responses.pop(0), usage={"total_tokens": 10})


def test_minimal_agent_generates_trace_and_report(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "README.md").write_text("hello\n", encoding="utf-8")
    run_root = tmp_path / "runs"
    client = FakeClient(
        [
            '{"thought": "inspect", "action": "read_file", "args": {"path": "README.md"}}',
            '{"thought": "done", "action": "finish", "args": {"answer": "read ok"}}',
        ]
    )

    result = MinimalCodingAgent(
        model_client=client,
        workspace=workspace,
        run_root=run_root,
        max_steps=3,
    ).run("Read the README.")

    assert result.success is True
    assert result.trace_path.exists()
    assert result.report_path.exists()
    events = read_trace(result.trace_path)
    assert any(event.event_type == EventType.FILE_READ for event in events)


class ErrorClient:
    def chat(self, messages, max_tokens=1200):
        del messages, max_tokens
        raise RuntimeError("Chat completion failed with HTTP 504")


def test_minimal_agent_records_model_errors(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = MinimalCodingAgent(
        model_client=ErrorClient(),
        workspace=workspace,
        run_root=tmp_path / "runs",
        max_steps=1,
    ).run("Do a task.")

    events = read_trace(result.trace_path)
    assert result.success is False
    assert result.report_path.exists()
    assert any("model_call_error" in event.audit_tags for event in events)

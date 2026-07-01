from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from trace2context.agent.loop import MinimalCodingAgent
from trace2context.agent.model import ChatModelClient
from trace2context.audit.analyzer import AuditAnalyzer
from trace2context.config import Settings
from trace2context.context.filter import AuditAwareFilter
from trace2context.reporting.markdown import render_audit_report
from trace2context.trace.logger import read_trace

app = typer.Typer(help="Trace2Context command line tools.")
console = Console()


@app.command()
def analyze(trace_path: Path) -> None:
    """Analyze a JSONL trace and print a compact summary."""
    events = read_trace(trace_path)
    result = AuditAnalyzer().analyze(events)
    console.print(result.to_table())


@app.command()
def report(trace_path: Path, output: Path = Path("audit_report.md")) -> None:
    """Analyze a JSONL trace and write a Markdown audit report."""
    events = read_trace(trace_path)
    analysis = AuditAnalyzer().analyze(events)
    filter_result = AuditAwareFilter().filter_events(events)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_audit_report(analysis, filter_result), encoding="utf-8")
    console.print(f"Wrote {output}")


@app.command()
def run(
    task: Annotated[str, typer.Argument(help="Coding task for the minimal agent.")],
    workspace: Annotated[
        Path,
        typer.Option(help="Workspace the agent may inspect and modify."),
    ] = Path("."),
    max_steps: Annotated[int, typer.Option(help="Maximum agent action steps.")] = 8,
    max_tokens: Annotated[int, typer.Option(help="Maximum model output tokens per step.")] = 800,
    timeout: Annotated[int, typer.Option(help="Model request timeout in seconds.")] = 45,
    retries: Annotated[int, typer.Option(help="Model request retry count.")] = 1,
    model: Annotated[str | None, typer.Option(help="Override TRACE2CONTEXT_MODEL.")] = None,
    api_mode: Annotated[
        str | None,
        typer.Option(help="Override TRACE2CONTEXT_API_MODE."),
    ] = None,
) -> None:
    """Run the minimal coding agent and generate trace/report artifacts."""
    settings = Settings.from_env().with_model(model).with_api_mode(api_mode)
    agent = MinimalCodingAgent(
        model_client=ChatModelClient(settings, timeout_seconds=timeout, max_retries=retries),
        workspace=workspace,
        max_steps=max_steps,
        model_max_tokens=max_tokens,
    )
    result = agent.run(task)
    console.print(f"Run: {result.run_id}")
    console.print(f"Success: {result.success}")
    if result.final_answer:
        console.print(f"Final answer: {result.final_answer}")
    console.print(f"Trace: {result.trace_path}")
    console.print(f"Report: {result.report_path}")

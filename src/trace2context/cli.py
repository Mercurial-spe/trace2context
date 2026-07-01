from pathlib import Path

import typer
from rich.console import Console

from trace2context.audit.analyzer import AuditAnalyzer
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

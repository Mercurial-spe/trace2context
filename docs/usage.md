# Usage

Install dependencies:

```bash
uv sync
```

Run tests:

```bash
uv run pytest
```

Analyze an example trace:

```bash
uv run trace2context analyze examples/simulated_traces/repeated_error.jsonl
```

Generate a Markdown audit report:

```bash
uv run trace2context report examples/simulated_traces/repeated_error.jsonl --output outputs/audit_report.md
```

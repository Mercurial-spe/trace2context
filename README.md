# Trace2Context

Trace2Context is a lightweight research prototype for audit-aware context
management in tool-using LLM agents.

The project records structured execution traces, analyzes tool calls and token
usage, and turns audit tags into context retention decisions.

## Scope

This repository is not a full agent framework or an observability SaaS. The MVP
focuses on a small, reproducible loop:

```text
agent/tool execution -> JSONL trace -> audit tags -> context filtering -> report
```

## Initial Modules

- `trace`: Pydantic schemas, JSONL trace logger, token estimation.
- `audit`: rule-based detection for failed tools, long outputs, repeated
  commands, repeated errors, and simulated tool calls.
- `context`: full-history, recent-N, and audit-aware filtering primitives.
- `reporting`: Markdown audit report generation.
- `tools`: minimal file and shell wrappers.
- `agent`: placeholder for a minimal ReAct-like coding agent loop.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
```

Run the CLI against a JSONL trace:

```bash
uv run trace2context analyze examples/simulated_traces/repeated_error.jsonl
```

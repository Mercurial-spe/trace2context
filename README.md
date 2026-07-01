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

Run the minimal coding agent:

```bash
cp .env.example .env
# edit .env with your OpenAI-compatible endpoint and key
# default API mode is /v1/responses with TRACE2CONTEXT_MODEL=gpt-5.4
uv run trace2context run \
  --workspace examples/toy_python_bug \
  --max-steps 8 \
  "Fix the failing test."
```

Agent runs write ignored local artifacts under `runs/<run_id>/`, including
`trace.jsonl` and `audit_report.md`.

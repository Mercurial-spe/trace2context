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
- `agent`: minimal coding agent loop with JSON actions and model/tool tracing.

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

Generate a Markdown audit report:

```bash
uv run trace2context report examples/simulated_traces/pipeline_masked_failure.jsonl \
  --output outputs/pipeline_masked_failure_report.md
```

Run the minimal coding agent:

```bash
cp .env.example .env
# edit .env with your OpenAI-compatible endpoint and key
rm -rf /tmp/trace2context-agent-demo
cp -R examples/toy_python_bug /tmp/trace2context-agent-demo
uv run trace2context run \
  --workspace /tmp/trace2context-agent-demo \
  --model deepseek-chat \
  --api-mode chat_completions \
  --max-steps 10 \
  "Fix failing test."
```

Agent runs write ignored local artifacts under `runs/<run_id>/`, including
`trace.jsonl` and `audit_report.md`.

The command above uses a copied workspace so the tracked example fixture remains
unchanged.

Compare context strategies for a recorded trace:

```bash
uv run trace2context compare runs/<run_id>/trace.jsonl \
  --recent-n 4 \
  --token-budget 300
```

The `examples/simulated_traces/` directory includes small fixtures for repeated
errors, masked pipeline failures, and assistant tool-claim hallucination.

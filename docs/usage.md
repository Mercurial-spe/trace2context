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

Run the minimal coding agent:

```bash
cp .env.example .env
# Edit .env with OPENAI_BASE_URL, OPENAI_API_KEY, TRACE2CONTEXT_MODEL,
# and TRACE2CONTEXT_API_MODE. The default mode is /v1/responses.
uv run trace2context run \
  --workspace examples/toy_python_bug \
  --max-steps 8 \
  "Fix the failing test."
```

The run command creates ignored local artifacts under `runs/<run_id>/`.

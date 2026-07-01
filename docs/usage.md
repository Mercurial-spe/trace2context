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
# and TRACE2CONTEXT_API_MODE.
rm -rf /tmp/trace2context-agent-demo
cp -R examples/toy_python_bug /tmp/trace2context-agent-demo
uv run trace2context run \
  --workspace /tmp/trace2context-agent-demo \
  --model deepseek-chat \
  --api-mode chat_completions \
  --max-steps 10 \
  "Fix failing test."
```

The run command creates ignored local artifacts under `runs/<run_id>/`.

For DeepSeek, use:

```env
OPENAI_BASE_URL=https://api.deepseek.com
TRACE2CONTEXT_MODEL=deepseek-chat
TRACE2CONTEXT_API_MODE=chat_completions
```

Compare context strategies for a trace:

```bash
uv run trace2context compare runs/<run_id>/trace.jsonl \
  --recent-n 4 \
  --token-budget 300
```

This prints a table comparing:

- `full_history`
- `recent_N`
- `audit_aware`

# Trace Schema

Trace2Context stores one JSON object per line. The primary event model is
`TraceEvent`.

Required fields:

- `run_id`: logical run/session id.
- `step_id`: monotonic step number inside a run.
- `event_type`: `message`, `tool_call`, `tool_result`, `file_read`,
  `file_write`, `llm_call`, `context_decision`, or `error`.

Important optional fields:

- `role`: `system`, `user`, `assistant`, or `tool`.
- `content`: message or general event text.
- `tool_name`: tool identifier such as `shell` or `read_file`.
- `tool_input`: string or structured tool arguments.
- `status`: `success`, `failed`, or `skipped`.
- `exit_code`: process exit code for shell-like tools.
- `stdout` / `stderr`: captured tool output.
- `duration_ms`: measured tool execution duration.
- `files_touched`: paths read or modified during a step.
- `token_count`: estimated token count for this event.
- `audit_tags`: tags produced by the analyzer.
- `metadata`: extension point for experiments and adapters.

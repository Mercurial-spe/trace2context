# Trace2Context Design Notes

## Position

Trace2Context is a lightweight audit-aware context management prototype for
tool-using LLM agents. It does not replace agent frameworks or observability
platforms. Its core contribution is turning execution traces into context
retention decisions.

## Pipeline

```text
User task
  -> minimal coding agent
  -> read_file / write_file / shell wrappers
  -> JSONL trace
  -> audit analyzer
  -> context filter for next prompt
  -> Markdown report / experiment metrics
```

## MVP Modules

- `trace.schema`: typed event and context decision contracts.
- `trace.logger`: append-only JSONL trace persistence.
- `audit.analyzer`: rule-based audit tags.
- `context.filter`: keep/compress/drop decisions.
- `reporting.markdown`: human-readable audit summary.
- `tools`: file and shell wrappers for future live runs.
- `agent`: JSON action protocol, OpenAI-compatible model client, and minimal
  coding loop.

The agent keeps complete tool outputs in the JSONL trace, but only feeds the
model a filtered context view. Long or repetitive outputs can be compressed or
dropped from the next prompt while remaining available for audit reports.

## Initial Audit Tags

- `failed_tool_call`
- `failed_test_command`
- `long_tool_output`
- `pipeline_command`
- `repeated_command`
- `repeated_error`
- `successful_test_command`
- `modified_file`
- `possible_tool_hallucination`

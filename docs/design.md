# Trace2Context Design Notes

## Position

Trace2Context is a lightweight audit-aware context management prototype for
tool-using LLM agents. It does not replace agent frameworks or observability
platforms. Its core contribution is turning execution traces into context
retention decisions.

## Pipeline

```text
Tool-using agent
  -> tool wrappers
  -> JSONL trace
  -> audit analyzer
  -> context filter
  -> Markdown report / experiment metrics
```

## MVP Modules

- `trace.schema`: typed event and context decision contracts.
- `trace.logger`: append-only JSONL trace persistence.
- `audit.analyzer`: rule-based audit tags.
- `context.filter`: keep/compress/drop decisions.
- `reporting.markdown`: human-readable audit summary.
- `tools`: file and shell wrappers for future live runs.

## Initial Audit Tags

- `failed_tool_call`
- `long_tool_output`
- `repeated_command`
- `repeated_error`
- `successful_test_command`
- `modified_file`
- `possible_tool_hallucination`

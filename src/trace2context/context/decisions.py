from trace2context.trace.schema import ContextAction

KEEP_REASONS = {
    "root_task": "root objective",
    "project_rule": "project or system rule",
    "latest_error": "latest unresolved failure evidence",
    "failed_test": "failed test evidence",
    "successful_test": "successful validation command",
    "modified_file": "file changed during the run",
}

COMPRESS_REASONS = {
    "long_output": "long tool output can be summarized",
    "repeated_error": "same error appeared multiple times",
    "old_tool_output": "old tool output is lower value than its status",
}

DROP_REASONS = {
    "duplicate": "duplicate low-value history",
    "stale_success": "old successful output without new information",
}

DEFAULT_PRIORITY = {
    ContextAction.KEEP: 100,
    ContextAction.COMPRESS: 50,
    ContextAction.DROP: 0,
}

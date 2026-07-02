from __future__ import annotations

import hashlib
import re
from collections import Counter

from trace2context.trace.schema import EventType, ToolStatus, TraceEvent
from trace2context.trace.token_counter import count_tokens

FAILED_TOOL_CALL = "failed_tool_call"
FAILED_TEST_COMMAND = "failed_test_command"
LONG_TOOL_OUTPUT = "long_tool_output"
PIPELINE_COMMAND = "pipeline_command"
REPEATED_COMMAND = "repeated_command"
REPEATED_ERROR = "repeated_error"
SUCCESSFUL_TEST_COMMAND = "successful_test_command"
MODIFIED_FILE = "modified_file"
POSSIBLE_TOOL_HALLUCINATION = "possible_tool_hallucination"

TOOL_CLAIM_PATTERNS = [
    re.compile(
        r"\bI (will|am going to|need to) use\b.*\b(tool|shell|read_file|write_file)\b",
        re.I,
    ),
    re.compile(r"\b(call|invoke|use)\s+[`'\"]?(shell|read_file|write_file|grep|web_fetch)", re.I),
    re.compile(r"\{[^{}]*[\"']tool[\"']\s*:", re.I),
    re.compile(r"(调用|使用).{0,16}(工具|shell|read_file|write_file|grep)"),
]

TEST_COMMAND_PATTERN = re.compile(r"\b(pytest|npm test|pnpm test|yarn test|go test|cargo test)\b")
TEST_FAILURE_OUTPUT_PATTERN = re.compile(
    r"(=+\s+FAILURES\s+=+|FAILED\s+\S+|ERROR collecting|failed in \d|\b\d+\s+failed\b)",
    re.I,
)


def normalize_command(command: str) -> str:
    return " ".join(command.strip().split())


def error_fingerprint(text: str) -> str:
    normalized = re.sub(r"0x[0-9a-fA-F]+|\d+", "<n>", text.strip())
    normalized = "\n".join(line.strip() for line in normalized.splitlines() if line.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def tag_failed_tool_call(event: TraceEvent) -> None:
    if event.event_type != EventType.TOOL_RESULT:
        return
    if event.status == ToolStatus.FAILED or (event.exit_code is not None and event.exit_code != 0):
        event.with_tag(FAILED_TOOL_CALL)


def tag_long_tool_output(event: TraceEvent, threshold_tokens: int = 800) -> None:
    if event.event_type != EventType.TOOL_RESULT:
        return
    output_tokens = event.token_count or count_tokens(event.output_text)
    event.token_count = output_tokens
    if output_tokens >= threshold_tokens:
        event.with_tag(LONG_TOOL_OUTPUT)


def tag_successful_test_command(event: TraceEvent) -> None:
    if event.event_type != EventType.TOOL_RESULT or event.tool_name != "shell":
        return
    command = str(event.tool_input or "")
    if (
        event.status == ToolStatus.SUCCESS
        and TEST_COMMAND_PATTERN.search(command)
        and not _looks_like_failed_test_output(event)
    ):
        event.with_tag(SUCCESSFUL_TEST_COMMAND)


def tag_failed_test_command(event: TraceEvent) -> None:
    if event.event_type != EventType.TOOL_RESULT or event.tool_name != "shell":
        return
    command = str(event.tool_input or "")
    failed = event.status == ToolStatus.FAILED or (
        event.exit_code is not None and event.exit_code != 0
    ) or _looks_like_failed_test_output(event)
    if failed and TEST_COMMAND_PATTERN.search(command):
        event.with_tag(FAILED_TEST_COMMAND)


def tag_pipeline_command(event: TraceEvent) -> None:
    if event.event_type != EventType.TOOL_RESULT or event.tool_name != "shell":
        return
    command = str(event.tool_input or "")
    if "|" in command:
        event.with_tag(PIPELINE_COMMAND)


def tag_modified_file(event: TraceEvent) -> None:
    if event.event_type == EventType.FILE_WRITE:
        event.with_tag(MODIFIED_FILE)


def tag_possible_tool_hallucination(event: TraceEvent) -> None:
    if event.event_type != EventType.MESSAGE:
        return
    if event.role and event.role.value != "assistant":
        return
    if any(pattern.search(event.content) for pattern in TOOL_CLAIM_PATTERNS):
        event.with_tag(POSSIBLE_TOOL_HALLUCINATION)


def tag_repeated_commands(events: list[TraceEvent]) -> None:
    shell_events = [
        event
        for event in events
        if (
            event.event_type == EventType.TOOL_RESULT
            and event.tool_name == "shell"
            and event.tool_input
        )
    ]
    counts = Counter(normalize_command(str(event.tool_input)) for event in shell_events)
    for event in shell_events:
        if counts[normalize_command(str(event.tool_input))] >= 2:
            event.with_tag(REPEATED_COMMAND)


def tag_repeated_errors(events: list[TraceEvent]) -> None:
    failed = [
        event
        for event in events
        if FAILED_TOOL_CALL in event.audit_tags and (event.stderr or event.stdout or event.content)
    ]
    fingerprints = Counter(
        error_fingerprint(event.stderr or event.stdout or event.content) for event in failed
    )
    for event in failed:
        fingerprint = error_fingerprint(event.stderr or event.stdout or event.content)
        if fingerprints[fingerprint] >= 2:
            event.with_tag(REPEATED_ERROR)


def _looks_like_failed_test_output(event: TraceEvent) -> bool:
    return bool(TEST_FAILURE_OUTPUT_PATTERN.search(event.stdout or event.stderr or event.content))

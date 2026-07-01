from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

VALID_ACTIONS = {"read_file", "write_file", "shell", "finish"}


class ActionParseError(ValueError):
    pass


@dataclass(frozen=True)
class AgentAction:
    action: str
    args: dict[str, Any] = field(default_factory=dict)
    thought: str = ""


def parse_action(text: str) -> AgentAction:
    data = _loads_json_object(text)
    action = data.get("action") or data.get("tool")
    if not isinstance(action, str):
        raise ActionParseError("Action JSON must contain an `action` string.")
    if action not in VALID_ACTIONS:
        raise ActionParseError(f"Unsupported action `{action}`.")

    args = data.get("args") or data.get("arguments") or _flat_args(data, action)
    if not isinstance(args, dict):
        raise ActionParseError("Action `args` must be an object.")
    thought = data.get("thought", "")
    return AgentAction(action=action, args=args, thought=str(thought))


def _loads_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
        if match:
            stripped = match.group(1)

    decoder = json.JSONDecoder()
    try:
        data, _ = decoder.raw_decode(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, re.DOTALL)
        if not match:
            raise ActionParseError("No JSON object found in assistant output.") from None
        try:
            data, _ = decoder.raw_decode(match.group(0))
        except json.JSONDecodeError as exc:
            raise ActionParseError(f"Invalid action JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ActionParseError("Assistant output must be a JSON object.")
    return data


def _flat_args(data: dict[str, Any], action: str) -> dict[str, Any]:
    if action == "read_file" and "path" in data:
        return {"path": data["path"]}
    if action == "write_file":
        return {key: data[key] for key in ["path", "content"] if key in data}
    if action == "shell" and "command" in data:
        return {"command": data["command"]}
    if action == "finish" and "answer" in data:
        return {"answer": data["answer"]}
    return {}

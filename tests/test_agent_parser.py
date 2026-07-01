import pytest

from trace2context.agent.parser import ActionParseError, parse_action


def test_parse_action_from_json():
    action = parse_action(
        '{"thought": "inspect file", "action": "read_file", "args": {"path": "README.md"}}'
    )

    assert action.action == "read_file"
    assert action.args["path"] == "README.md"


def test_parse_action_from_fenced_json():
    action = parse_action(
        '```json\n{"thought": "done", "action": "finish", "args": {"answer": "ok"}}\n```'
    )

    assert action.action == "finish"
    assert action.args["answer"] == "ok"


def test_parse_action_accepts_first_concatenated_json_object():
    action = parse_action(
        '{"action":"shell","args":{"command":"pytest"}}'
        '{"action":"shell","args":{"command":"pytest"}}'
    )

    assert action.action == "shell"
    assert action.args["command"] == "pytest"


def test_parse_action_accepts_flat_shell_command():
    action = parse_action('{"action":"shell","command":"pytest"}')

    assert action.action == "shell"
    assert action.args["command"] == "pytest"


def test_parse_action_rejects_unknown_action():
    with pytest.raises(ActionParseError):
        parse_action('{"action": "delete_everything", "args": {}}')

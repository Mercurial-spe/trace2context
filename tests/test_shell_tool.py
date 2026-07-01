from trace2context.tools.shell import run_shell


def test_run_shell_uses_pipefail():
    result = run_shell("python3 -c 'import sys; sys.exit(7)' | head")

    assert result.exit_code == 7
    assert not result.succeeded

# this_file: tests/test_release.py
"""Exercise the local release handoff with Git and GitHub CLI stand-ins."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def release_script(tmp_path: Path):
    shutil.copy(ROOT / "publish.sh", tmp_path)
    tools = tmp_path / "bin"
    tools.mkdir()
    for command in ("dirname", "head"):
        (tools / command).symlink_to(shutil.which(command))

    scripts = {
        "git": """case "$1" in
  fetch) exit 0 ;;
  tag) echo v1.2.9 ;;
  rev-parse) echo abc123 ;;
  *) exit 99 ;;
esac""",
        "gh": """echo "$*" >> "$CALL_LOG"
case "$1 $2" in
  'repo view')
    case "$4" in
      nameWithOwner) echo example/pdf3md ;;
      defaultBranchRef) echo stable ;;
      *) exit 99 ;;
    esac ;;
  'workflow run') exit "$DISPATCH_EXIT" ;;
  'run list') exit 0 ;;
  *) exit 99 ;;
esac""",
        "sleep": "exit 0",
    }
    for name, script in scripts.items():
        path = tools / name
        path.write_text(f"#!/bin/sh\n{script}\n")
        path.chmod(0o755)

    def run(*args: str, dispatch_exit: int = 0) -> tuple[subprocess.CompletedProcess, list[str]]:
        log = tmp_path / "calls"
        env = {"PATH": str(tools), "CALL_LOG": str(log), "DISPATCH_EXIT": str(dispatch_exit)}
        result = subprocess.run(
            ["/bin/bash", "publish.sh", *args],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
        )
        return result, log.read_text().splitlines()

    return run


@pytest.mark.parametrize(("args", "tag"), [((), "v1.2.10"), (("v2.0.0",), "v2.0.0")])
def test_release_dispatches_tag_on_default_branch(release_script, args, tag):
    result, calls = release_script(*args)
    assert result.returncode == 0, result.stderr
    assert f"workflow run release.yml -R example/pdf3md --ref stable -f tag={tag}" in calls


def test_release_when_invalid_tag_then_rejects_before_dispatch(release_script):
    result, calls = release_script("1.2.3")
    assert result.returncode != 0
    assert "vMAJOR.MINOR.PATCH" in result.stderr
    assert not any(call.startswith("workflow run ") for call in calls)


def test_release_when_dispatch_fails_then_propagates_exit_status(release_script):
    result, calls = release_script("v1.2.3", dispatch_exit=7)
    assert result.returncode == 7
    assert calls[-1] == "workflow run release.yml -R example/pdf3md --ref stable -f tag=v1.2.3"

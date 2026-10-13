# this_file: tests/test_release.py
"""Release script contracts in disposable Git repositories; never upload to PyPI."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, check=False)


@pytest.fixture
def release_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(ROOT / "publish.sh", repo)
    shutil.copy(ROOT / "build.sh", repo)
    (repo / ".gitignore").write_text("dist/\nsrc/vexy_pdf3md/__version__.py\n")
    (repo / "pyproject.toml").write_text("[project]\nname='vexy-pdf3md'\n")
    for args in [
        ("git", "init", "-q"),
        ("git", "config", "user.name", "Release Test"),
        ("git", "config", "user.email", "test@example.invalid"),
        ("git", "add", "."),
        ("git", "commit", "-qm", "initial"),
    ]:
        assert run(*args, cwd=repo).returncode == 0
    tools = tmp_path / "bin"
    tools.mkdir()
    (tools / "uvx").write_text("""#!/bin/sh
echo uvx "$@" >> "$CALL_LOG"
case "$1" in
  gitnextver)
    if [ "${TAG_MODE:-tag}" = no-tag ]; then exit 0; fi
    git add -A
    git diff --cached --quiet || git commit -qm release
    git tag v1.2.3 ;;
  twine) exit "${TWINE_EXIT:-0}" ;;
esac
""")
    (tools / "uv").write_text("""#!/bin/sh
echo uv "$@" >> "$CALL_LOG"
case "$1" in
  build)
    mkdir -p dist
    touch dist/vexy_pdf3md-1.2.3-py3-none-any.whl dist/vexy_pdf3md-1.2.3.tar.gz ;;
  publish) exit "${UPLOAD_EXIT:-0}" ;;
esac
""")
    for binary in tools.iterdir():
        binary.chmod(0o755)
    env = dict(
        os.environ,
        PATH=str(tools) + os.pathsep + os.environ["PATH"],
        CALL_LOG=str(tmp_path / "calls"),
        TAG_MODE="tag",
        TWINE_EXIT="0",
        UPLOAD_EXIT="0",
    )
    (repo / "change.txt").write_text("source change to commit\n")
    return repo, env


def test_release_tags_builds_and_publishes_only_fresh_artifacts(release_repo):
    repo, env = release_repo
    (repo / "dist").mkdir()
    (repo / "dist" / "unrelated.whl").write_text("must not upload")
    result = run("bash", "publish.sh", cwd=repo, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    calls = Path(env["CALL_LOG"]).read_text()
    assert "uvx gitnextver" in calls
    assert "uv build" in calls
    assert "uvx twine check" in calls
    assert "uv publish dist/vexy_pdf3md-1.2.3" in calls
    assert "unrelated.whl" not in calls, "stale dist/ artifacts must be removed before upload"
    assert not run("git", "status", "--porcelain", cwd=repo).stdout


@pytest.mark.parametrize("setting,value", [("TAG_MODE", "no-tag"), ("TWINE_EXIT", "1")])
def test_release_failure_prevents_upload(release_repo, setting, value):
    repo, env = release_repo
    env[setting] = value
    result = run("bash", "publish.sh", cwd=repo, env=env)
    assert result.returncode != 0
    assert "uv publish" not in Path(env["CALL_LOG"]).read_text()


def test_release_propagates_upload_failure(release_repo):
    repo, env = release_repo
    env["UPLOAD_EXIT"] = "7"
    result = run("bash", "publish.sh", cwd=repo, env=env)
    assert result.returncode == 7

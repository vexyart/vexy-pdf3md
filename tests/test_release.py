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
    (repo / ".gitignore").write_text("dist/\n.release-dist/\nsrc/vexy_pdf3md/__version__.py\n")
    (repo / "pyproject.toml").write_text("[project]\nname='vexy-pdf3md'\n")
    (repo / "test.sh").write_text("#!/bin/sh\nexit ${TEST_EXIT:-0}\n")
    (repo / "test.sh").chmod(0o755)
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
if [ "${TAG_MODE:-tag}" = no-tag ]; then exit 0; fi
git add -A
git diff --cached --quiet || git commit -qm release
git tag v1.2.3
""")
    (tools / "uv").write_text("""#!/usr/bin/env python3
import os, pathlib, subprocess, sys, zipfile, tarfile, io
with open(os.environ['CALL_LOG'], 'a') as f: f.write('uv ' + ' '.join(sys.argv[1:]) + '\\n')
if sys.argv[1] == 'build':
    folder = pathlib.Path(sys.argv[sys.argv.index('--out-dir') + 1]); folder.mkdir(exist_ok=True)
    version = os.environ.get('ARTIFACT_VERSION', '1.2.3')
    metadata = 'Metadata-Version: 2.4\\nName: vexy-pdf3md\\nVersion: ' + version + '\\n'
    with zipfile.ZipFile(folder / ('vexy_pdf3md-' + version + '-py3-none-any.whl'), 'w') as z:
        z.writestr('vexy_pdf3md-' + version + '.dist-info/METADATA', metadata)
        z.writestr('vexy_pdf3md/__version__.py', '__version__ = ' + repr(version))
    with tarfile.open(folder / ('vexy_pdf3md-' + version + '.tar.gz'), 'w:gz') as t:
        data = metadata.encode(); info = tarfile.TarInfo('vexy_pdf3md-' + version + '/PKG-INFO')
        info.size = len(data); t.addfile(info, io.BytesIO(data))
elif sys.argv[1] == 'run':
    index = sys.argv.index('python'); sys.exit(subprocess.call([sys.executable] + sys.argv[index + 1:]))
elif sys.argv[1] == 'publish':
    sys.exit(int(os.environ.get('UPLOAD_EXIT', '0')))
""")
    for binary in tools.iterdir():
        binary.chmod(0o755)
    env = dict(
        os.environ,
        PATH=str(tools) + os.pathsep + os.environ["PATH"],
        CALL_LOG=str(tmp_path / "calls"),
        PUBLISH_SKIP_UPLOAD="0",
        TEST_EXIT="0",
        TAG_MODE="tag",
        ARTIFACT_VERSION="1.2.3",
        UPLOAD_EXIT="0",
    )
    (repo / "change.txt").write_text("source change to commit\n")
    return repo, env


def test_release_commits_tags_and_publishes_only_fresh_artifacts(release_repo):
    repo, env = release_repo
    (repo / "dist").mkdir()
    (repo / "dist" / "unrelated.whl").write_text("must not upload")
    result = run("bash", "publish.sh", cwd=repo, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    calls = Path(env["CALL_LOG"]).read_text()
    assert "uvx gitnextver" in calls
    assert "uv publish" in calls
    assert "unrelated.whl" not in calls
    assert not run("git", "status", "--porcelain", cwd=repo).stdout


@pytest.mark.parametrize(
    "setting,value", [("TEST_EXIT", "1"), ("TAG_MODE", "no-tag"), ("ARTIFACT_VERSION", "9.9.9")]
)
def test_release_failure_prevents_upload(release_repo, setting, value):
    repo, env = release_repo
    env[setting] = value
    result = run("bash", "publish.sh", cwd=repo, env=env)
    assert result.returncode != 0
    assert "uv publish" not in Path(env["CALL_LOG"]).read_text()


def test_release_skip_upload_and_propagate_upload_failure(release_repo):
    repo, env = release_repo
    env["PUBLISH_SKIP_UPLOAD"] = "1"
    result = run("bash", "publish.sh", cwd=repo, env=env)
    assert result.returncode == 0, result.stderr
    assert "uv publish" not in Path(env["CALL_LOG"]).read_text()
    env.pop("PUBLISH_SKIP_UPLOAD")
    env["TAG_MODE"] = "no-tag"  # clean tagged retry
    env["UPLOAD_EXIT"] = "7"
    result = run("bash", "publish.sh", cwd=repo, env=env)
    assert result.returncode == 7


def test_release_untracks_generated_version(release_repo):
    repo, env = release_repo
    version = repo / "src/vexy_pdf3md/__version__.py"
    version.parent.mkdir(parents=True)
    version.write_text("__version__ = 'old'\n")
    assert run("git", "add", "-f", str(version), cwd=repo).returncode == 0
    assert run("git", "commit", "-qm", "old generated file", cwd=repo).returncode == 0
    env["PUBLISH_SKIP_UPLOAD"] = "1"
    result = run("bash", "publish.sh", cwd=repo, env=env)
    assert result.returncode == 0, result.stderr
    assert not run("git", "ls-files", "src/vexy_pdf3md/__version__.py", cwd=repo).stdout


def test_rejected_remote_push_blocks_upload(release_repo):
    repo, env = release_repo
    remote = repo.parent / "remote.git"
    assert run("git", "init", "--bare", str(remote), cwd=repo).returncode == 0
    assert run("git", "remote", "add", "origin", str(remote), cwd=repo).returncode == 0
    assert run("git", "push", "-u", "origin", "HEAD", cwd=repo).returncode == 0
    hook = remote / "hooks/pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    result = run("bash", "publish.sh", cwd=repo, env=env)
    assert result.returncode != 0
    assert "uv publish" not in Path(env["CALL_LOG"]).read_text()

# this_file: tests/test_failures.py
"""Publication, process boundaries, and path conflicts must fail without data loss."""

import json
import os
import subprocess
import sys
from dataclasses import asdict

import pytest

from vexy_pdf3md import convert
from vexy_pdf3md.models import Options
from vexy_pdf3md.paths import Job, _check_collisions
from vexy_pdf3md.process import ConversionError, run_worker
from vexy_pdf3md.publication import MARKER, publish


def test_casefold_output_collision(tmp_path):
    jobs = [
        Job(tmp_path / "a.pdf", tmp_path / "a.md", "auto"),
        Job(tmp_path / "a.PDF", tmp_path / "A.md", "auto"),
    ]
    with pytest.raises(ValueError, match="collision"):
        _check_collisions(jobs, Options())


def test_publication_refuses_unowned_media(tmp_path):
    output = tmp_path / "book.md"
    output.write_text("curated")
    output.with_suffix("").mkdir()
    (output.with_suffix("") / "photo.png").write_bytes(b"curated")
    staging = tmp_path / "stage"
    staging.mkdir()
    staged = staging / "result.md"
    staged.write_text("new")
    media = staging / "book"
    media.mkdir()
    with pytest.raises(FileExistsError):
        publish(staged, output, media, overwrite=True)
    assert output.read_text() == "curated"
    assert (output.with_suffix("") / "photo.png").read_bytes() == b"curated"


def test_publish_rolls_back_media_on_markdown_failure(tmp_path, monkeypatch):
    output = tmp_path / "book.md"
    output.write_text("original")
    assets = output.with_suffix("")
    assets.mkdir()
    (assets / MARKER).write_text("owned")
    (assets / "old.png").write_bytes(b"old")
    stage = tmp_path / "stage"
    stage.mkdir()
    staged = stage / "result.md"
    staged.write_text("new")
    media = stage / "book"
    media.mkdir()
    (media / "new.png").write_bytes(b"new")

    def denied(*args):
        raise PermissionError("injected write failure")

    monkeypatch.setattr(os, "replace", denied)
    with pytest.raises(PermissionError):
        publish(staged, output, media, overwrite=True)
    assert output.read_text() == "original"
    assert (assets / "old.png").read_bytes() == b"old"
    assert not (assets / "new.png").exists()


def test_worker_invalid_pdf_and_tiny_deadline(tmp_path):
    request = {
        "source": str(tmp_path / "missing.pdf"),
        "options": asdict(Options()),
        "action": "inspect",
    }
    with pytest.raises(ConversionError):
        run_worker(request, tmp_path, 10)
    with pytest.raises(subprocess.TimeoutExpired):
        run_worker(request, tmp_path, 0.00001)


def test_cli_batch_failure_nonzero_and_json(tmp_path):
    pdf = tmp_path / "bad.pdf"
    pdf.write_text("invalid")
    proc = subprocess.run(
        [sys.executable, "-m", "vexy_pdf3md", "--input", str(pdf)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["failed"] == 1


def test_cli_invalid_options_return_two_without_files(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-m", "vexy_pdf3md", "--input", str(tmp_path), "--workers=0"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert "workers" in json.loads(proc.stdout)["error"]
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("options", [{"overwrite": "False"}, {"fallback": 1}, {"password": 123}])
def test_ambiguous_option_types_cannot_authorize_writes(options):
    with pytest.raises(ValueError):
        Options(**options)


def test_output_must_be_markdown_and_symlink_is_rejected(tmp_path, scan):
    with pytest.raises(ValueError, match=".md"):
        convert(scan, tmp_path / "wrong.pdf")
    output = tmp_path / "link.md"
    output.symlink_to(scan)
    with pytest.raises(ValueError):
        convert(scan, output)


def test_bad_pages_preserve_existing_output(scan):
    output = scan.with_suffix(".md")
    output.write_text("keep")
    result = convert(scan, pages="999", overwrite=True)
    assert not result.ok
    assert output.read_text() == "keep"


def test_media_cannot_disguise_empty_text(scan):
    result = convert(scan, strategies="pymupdf", ocr="never", media="pages", fallback=False)
    assert not result.ok  # Rendering media cannot disguise an empty text conversion.
    assert not scan.with_suffix("").exists()


def test_worker_crash_ignores_stale_response(tmp_path, monkeypatch):
    executable = tmp_path / "crash"
    executable.write_text("#!/bin/sh\nexit 139\n")
    executable.chmod(0o755)
    (tmp_path / "response.json").write_text('{"stale": true}')
    monkeypatch.setattr("vexy_pdf3md.process.sys.executable", str(executable))
    with pytest.raises(ConversionError, match="exited 139"):
        run_worker({}, tmp_path, 10)


def test_cancel_stops_worker_promptly(tmp_path, monkeypatch):
    import time
    from concurrent.futures import CancelledError
    from threading import Event, Timer

    executable = tmp_path / "slow"
    executable.write_text("#!/bin/sh\nsleep 30\n")
    executable.chmod(0o755)
    monkeypatch.setattr("vexy_pdf3md.process.sys.executable", str(executable))
    cancel = Event()
    timer = Timer(0.2, cancel.set)
    timer.start()
    started = time.monotonic()
    try:
        with pytest.raises(CancelledError):
            run_worker({}, tmp_path, 20, cancel)
    finally:
        timer.cancel()
    assert time.monotonic() - started < 3

# this_file: src/vexy_pdf3md/process.py
"""Bound subprocess lifetimes, including child converters on POSIX hosts."""

import json
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import CancelledError
from pathlib import Path
from threading import Event


class ConversionError(RuntimeError):
    """One backend failed; another may still convert this document."""


def run_worker(request: dict, folder: Path, timeout: float, cancel: Event | None = None) -> dict:
    """Use stdin for secrets and a response file so library stdout cannot corrupt IPC."""
    response = folder / "response.json"
    if cancel is not None and cancel.is_set():
        raise CancelledError("conversion cancelled")
    response.unlink(missing_ok=True)
    command = [sys.executable, "-m", "vexy_pdf3md.worker", str(response)]
    with (folder / "worker.log").open("w+b") as log:
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=log,
            stderr=log,
            start_new_session=os.name == "posix",
        )
        try:
            _communicate(proc, json.dumps(request).encode(), timeout, cancel)
        except BaseException:
            _terminate(proc)
            raise
        if proc.returncode != 0 or not response.exists():
            log.seek(max(0, log.tell() - 2000))
            detail = log.read().decode("utf-8", errors="replace")[-1200:]
            raise ConversionError(f"worker exited {proc.returncode}: {detail.strip()}")
    result = json.loads(response.read_text())
    if "error" in result:
        raise ConversionError(result["error"])
    return result


def _communicate(proc: subprocess.Popen, data: bytes, timeout: float, cancel: Event | None) -> None:
    deadline = time.monotonic() + timeout
    pending = data
    while True:
        if cancel is not None and cancel.is_set():
            raise CancelledError("conversion cancelled")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(proc.args, timeout)
        try:
            proc.communicate(pending, timeout=min(remaining, 0.2))
            return
        except subprocess.TimeoutExpired:
            pending = None


def _terminate(proc: subprocess.Popen) -> None:
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except ProcessLookupError:
        pass
    proc.communicate()

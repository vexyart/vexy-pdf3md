# this_file: src/vexy_pdf3md/converter.py
"""Batch orchestration; threads only wait for isolated native worker processes."""

import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from threading import Event

from loguru import logger

from .models import OCR_STRATEGIES, STRATEGIES, Attempt, BatchResult, Options, Result
from .paths import Job, plan
from .process import ConversionError, run_worker
from .publication import publish
from .selection import candidates, check_quality


def convert(
    input: str | Path,
    output: str | Path | None = None,
    strategies: str | list[str] | tuple[str, ...] = "auto",
    media: bool | str = False,
    workers: int = 2,
    timeout: float = 600,
    fallback: bool = True,
    overwrite: bool = False,
    pages: str = "",
    password: str = "",
    lang: str = "eng",
    dpi: int = 150,
    ocr: str = "auto",
    min_text_ratio: float = 0.5,
) -> BatchResult:
    """Convert one PDF or a recursive tree; return per-output results and attempts.

    Configuration/path errors raise ValueError or OSError before processing.
    Document/backend failures are collected in the returned BatchResult.
    """
    names = (
        tuple(s.strip() for s in strategies.split(","))
        if isinstance(strategies, str)
        else tuple(strategies)
    )
    if names == ("all",):
        names = STRATEGIES
    media_mode = "images" if media is True else "none" if media is False else media
    options = Options(
        names,
        media_mode,
        workers,
        timeout,
        fallback,
        overwrite,
        str(pages),
        password,
        lang,
        dpi,
        ocr,
        min_text_ratio,
    )
    jobs = plan(input, output, options)
    cancel = Event()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        try:
            results = list(pool.map(lambda job: _convert_job(job, options, cancel), jobs))
        except BaseException:
            cancel.set()
            raise
    return BatchResult(results)


def _request(job: Job, options: Options, action: str, **extra: object) -> dict:
    return {
        "source": str(job.source),
        "options": asdict(options),
        "action": action,
        **extra,
    }


def _safe_error(exc: Exception, password: str) -> str:
    text = f"{type(exc).__name__}: {exc}"
    return text.replace(password, "[redacted]") if password else text


def _convert_job(job: Job, options: Options, cancel: Event) -> Result:
    result = Result(str(job.source), str(job.output), job.requested)
    if job.output.is_file() and not options.overwrite:
        result.status = "skipped"
        return result
    try:
        with tempfile.TemporaryDirectory(prefix="vexy-pdf3md-inspect-") as tmp:
            profile = run_worker(
                _request(job, options, "inspect"), Path(tmp), options.timeout, cancel
            )
        if profile["ocr_pages"] and not profile["needs_ocr"]:
            logger.warning(
                "{}: pages {} look scanned but the text layer is used; pass --ocr=always"
                " to OCR the whole document",
                job.source.name,
                profile["ocr_pages"],
            )
        engines = candidates(job.requested, profile, options)
        job.output.parent.mkdir(parents=True, exist_ok=True)
        for engine in engines:
            started = time.monotonic()
            try:
                _attempt(job, options, profile, engine, cancel)
            except Exception as exc:  # noqa: BLE001 - backend boundary; retain evidence and try next tool.
                error = _safe_error(exc, options.password)
                result.attempts.append(
                    Attempt(engine, "failed", round(time.monotonic() - started, 3), error)
                )
                logger.debug("{}: {} failed: {}", job.source.name, engine, error)
                continue
            result.attempts.append(Attempt(engine, "success", round(time.monotonic() - started, 3)))
            result.status, result.strategy = "success", engine
            if job.requested != "auto" and engine != job.requested:
                logger.warning(
                    "{}: {} failed; {} wrote {}", job.source.name, job.requested, engine, job.output
                )
            return result
        result.error = "all conversion strategies failed"
    except Exception as exc:  # noqa: BLE001 - one bad document must not abort the batch.
        result.error = _safe_error(exc, options.password)
    return result


def _attempt(job: Job, options: Options, profile: dict, engine: str, cancel: Event) -> None:
    needs_ocr = options.ocr == "always" or (profile["needs_ocr"] and options.ocr != "never")
    if needs_ocr and engine not in OCR_STRATEGIES:
        raise ConversionError("document needs OCR; this strategy only reads the text layer")
    if options.ocr == "never" and engine == "tesseract":
        raise ConversionError("Tesseract conflicts with ocr=never")
    with tempfile.TemporaryDirectory(prefix=".pdf3md-", dir=job.output.parent) as tmp:
        folder = Path(tmp)
        run_worker(
            _request(job, options, "convert", strategy=engine, profile=profile),
            folder,
            options.timeout,
            cancel,
        )
        staged = folder / "result.md"
        text = staged.read_text(encoding="utf-8")
        check_quality(text, profile, options)
        media = None
        if options.media != "none":
            scratch = folder / "assets-work"
            scratch.mkdir()
            exported = run_worker(
                _request(job, options, "media", basename=job.output.stem, profile=profile),
                scratch,
                options.timeout,
                cancel,
            )
            text += exported["markdown"]
            media = scratch / "media" / job.output.stem
        staged.write_text(text.strip() + "\n", encoding="utf-8")
        publish(staged, job.output, media, options.overwrite)

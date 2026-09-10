# this_file: src/vexy_pdf3md/cli.py
"""Fire CLI with JSON results and meaningful exit codes for shell batches."""

import json
import sys

import fire
from fire.decorators import SetParseFn
from loguru import logger

from .converter import convert


@SetParseFn(
    str, "input", "output", "strategies", "pages", "password", "language", "vision_languages", "ocr"
)
def command(
    input: str,
    output: str | None = None,
    strategies: str = "auto",
    media: bool | str = False,
    workers: int = 2,
    timeout: float = 600,
    fallback: bool = True,
    overwrite: bool = False,
    pages: str = "",
    password: str = "",
    language: str = "eng",
    vision_languages: str = "en",
    dpi: int = 150,
    ocr: str = "auto",
    min_text_ratio: float = 0.5,
    verbose: bool = False,
) -> None:
    """Convert a PDF or recursive PDF tree to Markdown.

    Args:
        input: PDF file or directory, traversed recursively (case-insensitive .pdf).
        output: Markdown file or output directory; defaults beside the input.
        strategies: auto, or comma-separated markit,pymupdf,pdf22md,tesseract,docling.
            Multiple strategies run independently and add .STRATEGY.md suffixes.
        media: True/images exports raster image placements; pages renders complete
            pages including vector graphics; False disables export.
        workers: Maximum simultaneous isolated jobs, from 1 to 64.
        timeout: Seconds per inspection, backend attempt, or media export.
        fallback: Try another strategy after failure (default True).
        overwrite: Replace existing Markdown and owned media (default False).
        pages: One-based inclusive selection, e.g. 1-3,5; empty means all pages.
        password: Password for encrypted PDFs, omitted from reports/logs.
        language: Tesseract/Docling language codes, e.g. eng+pol.
        vision_languages: pdf22md Vision languages, e.g. en,pl.
        dpi: OCR/media rendering resolution, 72 to 600.
        ocr: auto detects scans, always requires OCR, never uses text layers only.
        min_text_ratio: Minimum retained alphanumeric text-layer fraction (0-1).
        verbose: Emit backend failure details to stderr through loguru.
    """
    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if verbose else "WARNING")
    arguments = locals().copy()
    arguments.pop("verbose")
    try:
        result = convert(**arguments)
    except (ValueError, OSError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(2) from None
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if not result.ok:
        raise SystemExit(1)


def main() -> None:
    fire.Fire(command)

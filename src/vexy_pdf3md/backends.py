# this_file: src/vexy_pdf3md/backends.py
"""Small adapters for existing converters; called only inside isolated workers."""

import importlib
import importlib.machinery
import shutil
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path

import pymupdf

from .languages import parse, tessdata_dir, vision_codes
from .process import ConversionError


def external(command: list[str], folder: Path) -> str:
    """Parent worker deadline covers this subprocess and all of its descendants."""
    result = subprocess.run(command, capture_output=True, text=True, cwd=folder, check=False)
    if result.returncode:
        raise ConversionError(f"{command[0]} exited {result.returncode}: {result.stderr[-1000:]}")
    return result.stdout


def convert_backend(strategy: str, pdf: Path, folder: Path, options: dict, profile: dict) -> str:
    if strategy == "pymupdf":
        return native_markdown(pdf)
    if strategy == "markit":
        return external([executable("markit"), "-q", "--no-images", str(pdf)], folder)
    if strategy == "pdf22md":
        command = [
            executable("pdf22md"),
            "--input",
            str(pdf),
            "--output",
            str(folder / "native.md"),
            "--quiet",
            "--languages",
            vision_codes(options["lang"]),
            "--dpi",
            str(options["dpi"]),
        ]
        if options["ocr"] == "never" or (options["ocr"] == "auto" and not profile["needs_ocr"]):
            command.append("--fast")
        external(command, folder)
        return (folder / "native.md").read_text(encoding="utf-8")
    if strategy == "tesseract":
        return tesseract_markdown(pdf, folder, options)
    if strategy == "docling":
        return docling_markdown(pdf, options, profile)
    raise ValueError(f"unknown strategy {strategy}")


def executable(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise ConversionError(f"{name} is not installed or not on PATH")
    return path


def native_markdown(pdf: Path) -> str:
    """Basic blocks and font-size headings; markit is preferred for complex layouts."""
    with pymupdf.open(pdf) as doc:
        sizes: Counter = Counter()
        for page in doc:
            for block in page.get_text("dict", flags=pymupdf.TEXTFLAGS_TEXT)["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        sizes[round(span["size"])] += len(span["text"].strip())
        body = sizes.most_common(1)[0][0] if sizes else 12
        headings = sorted((s for s in sizes if s > body * 1.15), reverse=True)[:6]
        result = []
        for page in doc:
            blocks = []
            for block in page.get_text("dict", flags=pymupdf.TEXTFLAGS_TEXT, sort=True)["blocks"]:
                lines = block.get("lines", [])
                text = "\n".join(
                    "".join(s["text"] for s in line["spans"]) for line in lines
                ).strip()
                if not text:
                    continue
                size = max(round(s["size"]) for line in lines for s in line["spans"])
                prefix = "#" * (headings.index(size) + 1) + " " if size in headings else ""
                blocks.append(prefix + text)
            result.append("\n\n".join(blocks))
        return "\n\n---\n\n".join(result)


def tesseract_markdown(pdf: Path, folder: Path, options: dict) -> str:
    engine = executable("tesseract")
    codes = parse(options["lang"])
    tessdata = tessdata_dir(engine, codes)
    texts = []
    with pymupdf.open(pdf) as doc:
        for page in doc:
            raster = folder / "ocr.png"
            page.get_pixmap(dpi=options["dpi"], alpha=False).save(raster)
            texts.append(
                external(
                    [
                        engine,
                        str(raster),
                        "stdout",
                        "-l",
                        "+".join(codes),
                        "--tessdata-dir",
                        str(tessdata),
                    ],
                    folder,
                ).strip()
            )
            raster.unlink()
    return "\n\n---\n\n".join(texts)


def docling_markdown(pdf: Path, options: dict, profile: dict | None = None) -> str:
    _shield_torchaudio()
    try:
        from docling.datamodel.base_models import ConversionStatus, InputFormat
        from docling.datamodel.pipeline_options import (
            OcrMode,
            PdfPipelineOptions,
            TesseractCliOcrOptions,
        )
        from docling.document_converter import DocumentConverter, PdfFormatOption
    except ImportError as exc:
        raise ConversionError("docling is not installed; install vexy-pdf3md[docling]") from exc
    codes = parse(options["lang"])
    tesseract = shutil.which("tesseract")
    full_page = options["ocr"] == "always" or bool(profile and profile.get("needs_ocr"))
    pipeline = PdfPipelineOptions(do_ocr=options["ocr"] != "never")
    if tesseract:
        pipeline.ocr_options = TesseractCliOcrOptions(
            lang=codes,
            path=str(tessdata_dir(tesseract, codes)),
            # Docling only OCRs bitmap regions by default; an unreadable text layer would
            # otherwise be copied verbatim, so scans get whole-page OCR.
            mode=OcrMode.FULL_PAGE if full_page else OcrMode.DEFAULT,
            scale=options["dpi"] / 72,
        )
    result = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline)}
    ).convert(pdf)
    if result.status != ConversionStatus.SUCCESS:
        raise ConversionError(f"docling conversion incomplete: {result.status}")
    return result.document.export_to_markdown()


def _shield_torchaudio() -> None:
    """transformers imports torchaudio whenever it is installed; docling never needs it,
    so a native build mismatched with torch must not take layout analysis down."""
    try:
        importlib.import_module("torchaudio")
    except (ImportError, OSError):
        stub = types.ModuleType("torchaudio")
        stub.__spec__ = importlib.machinery.ModuleSpec("torchaudio", None)
        sys.modules["torchaudio"] = stub

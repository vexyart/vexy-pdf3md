# this_file: src/vexy_pdf3md/selection.py
"""Deterministic strategy ranking and conservative output checks."""

import importlib.util
import re
import shutil

from .models import OCR_STRATEGIES, Options
from .process import ConversionError


def available(strategy: str) -> bool:
    if strategy == "pymupdf":
        return True
    if strategy == "docling":
        return importlib.util.find_spec("docling") is not None
    return shutil.which(strategy) is not None


def candidates(requested: str, profile: dict, options: Options) -> list[str]:
    needs_ocr = options.ocr == "always" or (profile["needs_ocr"] and options.ocr != "never")
    ranked = (
        list(OCR_STRATEGIES)
        if needs_ocr
        else ["markit", "pymupdf", "pdf22md", "tesseract", "docling"]
    )
    if options.ocr == "never":
        ranked.remove("tesseract")
    if requested == "auto":
        ordered = [s for s in ranked if available(s)]
        if not ordered:
            raise ConversionError(
                "scanned PDF needs an OCR tool: install pdf22md, Tesseract, or vexy-pdf3md[docling]"
            )
    else:
        ordered = [requested] + [s for s in ranked if s != requested and available(s)]
    return ordered if options.fallback else ordered[:1]


def check_quality(text: str, profile: dict, options: Options) -> None:
    """Reject empty, corrupt, or heavily truncated output before media is added."""
    plain = re.sub(r"<!--.*?-->|!\[[^\]]*\]\([^)]*\)", "", text, flags=re.DOTALL)
    chars = sum(c.isalnum() for c in plain)
    if not chars:
        raise ConversionError("converter returned no usable text")
    if plain.count("\ufffd") > max(3, len(plain) * 0.02):
        raise ConversionError("converter returned replacement-character corruption")
    if chars < profile["characters"] * options.min_text_ratio:
        raise ConversionError(
            f"truncated output: {chars} characters vs {profile['characters']} in text layer"
        )

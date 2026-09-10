# this_file: src/vexy_pdf3md/models.py
"""Validated conversion options and serializable batch evidence."""

from dataclasses import asdict, dataclass, field
from math import isfinite
from typing import Literal

STRATEGIES = ("markit", "pymupdf", "pdf22md", "tesseract", "docling")
OCR_STRATEGIES = ("pdf22md", "tesseract", "docling")


@dataclass(frozen=True)
class Options:
    """Settings shared by each isolated attempt; passwords never enter reports."""

    strategies: tuple[str, ...] = ("auto",)
    media: str = "none"
    workers: int = 2
    timeout: float = 600
    fallback: bool = True
    overwrite: bool = False
    pages: str = ""
    password: str = field(default="", repr=False)
    language: str = "eng"
    vision_languages: str = "en"
    dpi: int = 150
    ocr: str = "auto"
    min_text_ratio: float = 0.5

    def __post_init__(self) -> None:
        if type(self.fallback) is not bool or type(self.overwrite) is not bool:
            raise ValueError("fallback and overwrite must be booleans")
        if not all(
            isinstance(value, str)
            for value in (self.password, self.pages, self.language, self.vision_languages)
        ):
            raise ValueError("password, pages, and language options must be strings")
        if not self.strategies or any(s not in (*STRATEGIES, "auto") for s in self.strategies):
            raise ValueError(f"strategies must be auto or a selection of {STRATEGIES}")
        if len(set(self.strategies)) != len(self.strategies) or (
            "auto" in self.strategies and len(self.strategies) > 1
        ):
            raise ValueError("auto must stand alone; strategies must be unique")
        if type(self.workers) is not int or not 1 <= self.workers <= 64:
            raise ValueError("workers must be an integer from 1 to 64")
        if isinstance(self.timeout, bool) or not isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        if type(self.dpi) is not int or not 72 <= self.dpi <= 600:
            raise ValueError("dpi must be an integer from 72 to 600")
        if not isfinite(self.min_text_ratio) or not 0 <= self.min_text_ratio <= 1:
            raise ValueError("min_text_ratio must be between 0 and 1")
        if self.media not in ("none", "images", "pages") or self.ocr not in (
            "auto",
            "always",
            "never",
        ):
            raise ValueError("invalid media or ocr mode")
        if not self.language or not self.vision_languages:
            raise ValueError("OCR language lists cannot be empty")


@dataclass
class Attempt:
    strategy: str
    status: Literal["success", "failed"]
    seconds: float
    error: str = ""


@dataclass
class Result:
    input: str
    output: str
    requested: str
    status: Literal["success", "failed", "skipped"] = "failed"
    strategy: str | None = None
    attempts: list[Attempt] = field(default_factory=list)
    error: str = ""


@dataclass
class BatchResult:
    results: list[Result]

    @property
    def ok(self) -> bool:
        return all(r.status != "failed" for r in self.results)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "succeeded": sum(r.status == "success" for r in self.results),
            "skipped": sum(r.status == "skipped" for r in self.results),
            "failed": sum(r.status == "failed" for r in self.results),
            "results": [asdict(r) for r in self.results],
        }

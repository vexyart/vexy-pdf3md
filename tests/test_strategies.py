# this_file: tests/test_strategies.py
"""Real converter integrations and deterministic failure injection."""

import os
import shutil
import sys

import pytest

from vexy_pdf3md import convert
from vexy_pdf3md.inspection import inspect, select_pages
from vexy_pdf3md.models import Options
from vexy_pdf3md.process import ConversionError
from vexy_pdf3md.selection import candidates, check_quality


@pytest.mark.parametrize("engine", ["tesseract", "pdf22md"])
def test_real_scanned_document_ocr(scan, engine):
    if not shutil.which(engine):
        pytest.skip(f"{engine} is not installed")
    result = convert(scan, strategies=engine, fallback=False, timeout=45)
    assert result.ok, result.to_dict()
    assert "quick brown fox" in scan.with_suffix(".md").read_text()


def test_scan_cannot_silently_use_text_only_backend(scan):
    result = convert(scan, strategies="pymupdf", fallback=False)
    assert not result.ok
    assert "needs OCR" in result.results[0].attempts[0].error
    assert not scan.with_suffix(".md").exists()


def test_scan_auto_selection_and_real_fallback(scan):
    if not shutil.which("tesseract"):
        pytest.skip("Tesseract is not installed")
    result = convert(scan, strategies="pymupdf")
    assert result.ok, result.to_dict()
    assert result.results[0].attempts[0].status == "failed"
    assert result.results[0].strategy in ("pdf22md", "tesseract", "docling")


@pytest.mark.parametrize("value", ["0", "3", "2-1", "-1", "1-x", "1,", "1-999999999999"])
def test_page_ranges_reject_invalid_values(value):
    with pytest.raises(ValueError):
        select_pages(value, 2)


def test_page_ranges_unique_in_document_order():
    assert select_pages("3,1-2,2", 3) == [0, 1, 2]


@pytest.mark.parametrize(
    "text,reason",
    [
        ("<!-- Image 1 -->", "no usable"),
        ("short", "truncated"),
        ("hello " + "\ufffd" * 10, "corruption"),
    ],
)
def test_quality_rejects_false_success(text, reason):
    with pytest.raises(ConversionError, match=reason):
        check_quality(text, {"characters": 100}, Options())


def test_strategy_ranking_with_missing_tools(monkeypatch):
    monkeypatch.setattr("vexy_pdf3md.selection.available", lambda name: name == "pymupdf")
    assert candidates("auto", {"needs_ocr": False}, Options()) == ["pymupdf"]
    with pytest.raises(ConversionError, match="OCR tool"):
        candidates("auto", {"needs_ocr": True}, Options())


@pytest.mark.parametrize(
    "script", ["print('tiny')", "raise SystemExit(7)", "import os; os._exit(139)"]
)
def test_backend_failures_fall_back_and_report_reason(tmp_path, monkeypatch, script):
    import pymupdf

    pdf = tmp_path / "text.pdf"
    with pymupdf.open() as doc:
        doc.new_page().insert_text(
            (72, 72),
            "A substantial paragraph for testing conversion failure and fallback behavior.",
        )
        doc.save(pdf)
    binary = tmp_path / "markit"
    binary.write_text(f"#!{sys.executable}\n{script}\n")
    binary.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    result = convert(pdf, strategies="markit")
    item = result.results[0]
    assert result.ok and item.strategy == "pymupdf", result.to_dict()
    assert [a.status for a in item.attempts] == ["failed", "success"]
    assert not list(tmp_path.glob(".pdf3md-*"))


def test_inspection_detects_scan_after_text_cover(scan, tmp_path):
    from dataclasses import asdict

    import pymupdf

    mixed = tmp_path / "mixed.pdf"
    with pymupdf.open() as doc, pymupdf.open(scan) as scan_doc:
        doc.new_page().insert_text((72, 72), "Text cover " * 10)
        doc.insert_pdf(scan_doc)
        doc.save(mixed)
    profile = inspect(str(mixed), asdict(Options()))
    assert profile["ocr_pages"] == [2]
    assert profile["needs_ocr"]
    assert profile["characters"] > 40


def test_isolated_image_page_does_not_force_whole_document_ocr(scan, tmp_path):
    from dataclasses import asdict

    import pymupdf

    mixed = tmp_path / "mostly-text.pdf"
    with pymupdf.open() as doc, pymupdf.open(scan) as scan_doc:
        for _ in range(5):
            doc.new_page().insert_text((72, 72), "Ordinary text page. " * 10)
        doc.insert_pdf(scan_doc)
        doc.save(mixed)
    profile = inspect(str(mixed), asdict(Options()))
    assert profile["ocr_pages"] == [6]
    assert not profile["needs_ocr"]
    result = convert(mixed, strategies="pymupdf", fallback=False)
    assert result.ok, result.to_dict()


def test_sibling_strategies_are_not_fallback_candidates(monkeypatch):
    monkeypatch.setattr("vexy_pdf3md.selection.available", lambda name: True)
    profile = {"needs_ocr": False}
    single = candidates("docling", profile, Options(strategies=("docling",)))
    assert single == ["docling", "markit", "pymupdf", "pdf22md", "tesseract"]
    paired = candidates("docling", profile, Options(strategies=("markit", "docling")))
    assert paired == ["docling", "pymupdf", "pdf22md", "tesseract"]


@pytest.mark.optional
def test_real_docling(scan):
    pytest.importorskip("docling")
    result = convert(scan, strategies="docling", fallback=False, timeout=120)
    assert result.ok, result.to_dict()
    assert "quick brown fox" in scan.with_suffix(".md").read_text()

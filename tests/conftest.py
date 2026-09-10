# this_file: tests/conftest.py
"""Small synthetic PDFs avoid dependence on private books or downloaded fixtures."""

from pathlib import Path

import pymupdf
import pytest


@pytest.fixture
def scan(tmp_path: Path) -> Path:
    path = tmp_path / "scan.pdf"
    with pymupdf.open() as original, pymupdf.open() as scanned:
        page = original.new_page(width=500, height=300)
        page.insert_text((35, 65), "Scanned document", fontsize=24)
        page.insert_text((35, 105), "The quick brown fox jumps over the lazy dog.", fontsize=16)
        raster = page.get_pixmap(dpi=150)
        scanned.new_page(width=500, height=300).insert_image(page.rect, pixmap=raster)
        scanned.save(path)
    return path

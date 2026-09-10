# this_file: tests/test_conversion.py
"""Observable conversion contracts, using real PDFs and isolated workers."""

import json
import subprocess
import sys
from urllib.parse import unquote

import pymupdf
import pytest

from vexy_pdf3md import convert


@pytest.fixture
def pdf(tmp_path):
    path = tmp_path / "A book.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 72), "A useful document", fontsize=22)
        page.insert_text((72, 110), "This paragraph contains enough text to verify extraction.")
        doc.save(path)
    return path


def test_single_default_and_existing_output(pdf):
    result = convert(pdf, strategies="pymupdf")
    assert result.ok
    assert "useful document" in pdf.with_suffix(".md").read_text()
    pdf.with_suffix(".md").write_text("curated")
    assert convert(pdf, strategies="pymupdf").results[0].status == "skipped"
    assert pdf.with_suffix(".md").read_text() == "curated"


def test_recursive_structure_uppercase_and_batch_failure(pdf, tmp_path):
    root = tmp_path / "input"
    (root / "nested").mkdir(parents=True)
    (root / "nested" / "Book.PDF").write_bytes(pdf.read_bytes())
    (root / "bad.pdf").write_text("not a PDF")
    output = tmp_path / "output"
    result = convert(root, output, strategies="pymupdf", workers=2)
    assert not result.ok
    assert len(result.results) == 2
    assert (output / "nested" / "Book.md").exists()
    assert not (output / "bad.md").exists()


def test_variants_have_separate_output_names(pdf):
    result = convert(pdf, strategies="pymupdf,markit", fallback=False)
    assert len(result.results) == 2
    assert pdf.with_name("A book.pymupdf.md").exists()
    assert not pdf.with_suffix(".md").exists()


def test_media_links_resolve_with_spaces(pdf):
    with pymupdf.open(pdf) as doc:
        pix = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 40, 40), False)
        pix.clear_with(120)
        doc[0].insert_image(pymupdf.Rect(72, 150, 160, 240), pixmap=pix)
        doc.saveIncr()
    result = convert(pdf, strategies="pymupdf", media=True)
    assert result.ok
    text = pdf.with_suffix(".md").read_text()
    links = [line.split("](", 1)[1][:-1] for line in text.splitlines() if line.startswith("![")]
    assert links
    for link in links:
        image = pdf.parent / unquote(link)
        assert image.parent == pdf.with_suffix("")
        assert pymupdf.Pixmap(str(image)).width > 0


@pytest.mark.parametrize("name", ["response.json.md", "input.pdf.md", "worker.log.md"])
def test_media_basename_cannot_collide_with_worker_files(pdf, tmp_path, name):
    output = tmp_path / name
    result = convert(pdf, output, strategies="pymupdf", media="pages", pages="1")
    assert result.ok, result.to_dict()
    assert (output.with_suffix("") / "page-0001-001.png").is_file()


def test_overwrite_removes_stale_generated_assets(pdf):
    assert convert(pdf, strategies="pymupdf", media="pages").ok
    stale = pdf.with_suffix("") / "stale.png"
    stale.write_bytes(b"old")
    assert convert(pdf, strategies="pymupdf", media="pages", overwrite=True).ok
    assert not stale.exists()


def test_rotated_page_exports_visible_image(tmp_path):
    pdf = tmp_path / "rotated.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page(width=300, height=500)
        page.insert_text((25, 50), "A rotated page with a visible image")
        pix = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 50, 50), False)
        pix.clear_with(80)
        page.insert_image(pymupdf.Rect(30, 350, 100, 420), pixmap=pix)
        page.set_rotation(90)
        doc.save(pdf)
    result = convert(pdf, strategies="pymupdf", media=True)
    assert result.ok, result.to_dict()
    images = list(pdf.with_suffix("").glob("*.png"))
    assert len(images) == 1, "rotation must not discard the image bounding box"
    pix = pymupdf.Pixmap(str(images[0]))
    assert min(pix.samples) < 200, "exported image must contain visible content"


@pytest.mark.parametrize("engine", ["markit", "pdf22md"])
def test_real_text_layer_backends(pdf, engine):
    import shutil

    if not shutil.which(engine):
        pytest.skip(f"{engine} not installed")
    result = convert(pdf, strategies=engine, fallback=False)
    assert result.ok, result.to_dict()
    assert result.results[0].strategy == engine
    assert "useful document" in pdf.with_suffix(".md").read_text()


def test_page_selection_and_password(pdf, tmp_path):
    locked = tmp_path / "locked.pdf"
    with pymupdf.open(pdf) as doc:
        doc.new_page().insert_text((72, 72), "Second page only")
        doc.save(
            locked,
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            owner_pw="owner",
            user_pw="secret",
        )
    assert not convert(locked, strategies="pymupdf").ok
    result = convert(locked, strategies="pymupdf", password="secret", pages="2")
    assert result.ok
    text = locked.with_suffix(".md").read_text()
    assert "Second page only" in text and "useful document" not in text


@pytest.mark.parametrize(
    "kwargs",
    [{"workers": 0}, {"timeout": -1}, {"strategies": "unknown"}, {"min_text_ratio": 2}],
)
def test_invalid_options_fail_before_writes(pdf, kwargs):
    with pytest.raises(ValueError):
        convert(pdf, **kwargs)
    assert not pdf.with_suffix(".md").exists()


def test_cli_json_and_exit_status(pdf):
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "vexy_pdf3md",
            "--input",
            str(pdf),
            "--strategies=pymupdf",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout)["succeeded"] == 1


def test_cli_numeric_password_and_comma_page_selection(pdf, tmp_path):
    locked = tmp_path / "number.pdf"
    with pymupdf.open(pdf) as doc:
        doc.new_page().insert_text((72, 72), "Second page selected")
        doc.save(locked, encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="123456")
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "vexy_pdf3md",
            "--input",
            str(locked),
            "--strategies=pymupdf",
            "--password=123456",
            "--pages=1,2",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "123456" not in run.stdout + run.stderr
    assert "Second page selected" in locked.with_suffix(".md").read_text()


def test_empty_directory_and_collision(tmp_path, pdf):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="PDF"):
        convert(empty)
    nested = pdf.with_suffix("")
    nested.mkdir()
    (nested / "nested.pdf").write_bytes(pdf.read_bytes())
    with pytest.raises(ValueError, match="collision"):
        convert(pdf.parent, media=True)

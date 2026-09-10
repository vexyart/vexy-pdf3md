# this_file: examples/smoke.py
"""Run with uv run examples/smoke.py; creates and verifies a temporary PDF tree."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pymupdf

from vexy_pdf3md import convert


def main() -> None:
    with TemporaryDirectory(prefix="pdf3md-example-") as tmp:
        root = Path(tmp)
        source = root / "input" / "nested" / "example.pdf"
        source.parent.mkdir(parents=True)
        with pymupdf.open() as doc:
            page = doc.new_page()
            page.insert_text((72, 72), "Example document", fontsize=22)
            page.insert_text((72, 110), "This PDF demonstrates recursive Markdown conversion.")
            doc.save(source)
        result = convert(root / "input", root / "output", strategies="pymupdf", media="pages")
        output = root / "output" / "nested" / "example.md"
        assert result.ok, result.to_dict()
        assert "Example document" in output.read_text(), "text was not extracted"
        assert (output.with_suffix("") / "page-0001-001.png").is_file(), "media missing"
        print("Verified nested/example.md and its rendered page image.")


if __name__ == "__main__":
    main()

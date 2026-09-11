# this_file: src/vexy_pdf3md/inspection.py
"""PDF inspection executed exclusively in a worker process."""

from pathlib import Path

import pymupdf

# Whole-document OCR is required only when this share of selected pages looks scanned.
# One screenshot page in a long text document must not send the text layer through OCR.
OCR_PAGE_SHARE = 0.2


def select_pages(value: str, count: int) -> list[int]:
    """Parse one-based inclusive ranges, preserving document order without duplicates."""
    if not value:
        return list(range(count))
    pages: set[int] = set()
    for part in str(value).split(","):
        ends = part.strip().split("-")
        if len(ends) > 2 or not all(e.strip().isdigit() for e in ends):
            raise ValueError("pages must be a list such as 1-3,5")
        first, last = int(ends[0]), int(ends[-1])
        if not 1 <= first <= last <= count:
            raise ValueError(f"page range {part!r} is outside 1-{count}")
        pages.update(range(first - 1, last))
    return sorted(pages)


def open_pdf(source: str, password: str = "") -> pymupdf.Document:
    doc = pymupdf.open(source)
    if not doc.is_pdf or not doc.page_count:
        doc.close()
        raise ValueError("input is not a nonempty PDF")
    if doc.needs_pass and not doc.authenticate(password):
        doc.close()
        raise ValueError("PDF needs a valid password")
    return doc


def inspect(source: str, options: dict) -> dict:
    """Check every selected page: covers with text must not conceal scanned interiors.

    Pages that look scanned are always listed in ``ocr_pages``; ``needs_ocr`` is set only
    when they reach ``OCR_PAGE_SHARE`` of the selection. Use ``ocr=always`` otherwise.
    """
    counts, scanned = [], []
    with open_pdf(source, options["password"]) as doc:
        pages = select_pages(options["pages"], len(doc))
        for index in pages:
            page = doc[index]
            text = page.get_text()
            chars = sum(c.isalnum() for c in text)
            images = page.get_image_info()
            largest = max(
                (pymupdf.Rect(i["bbox"]).get_area() / max(1, page.rect.get_area()) for i in images),
                default=0,
            )
            suspect = (chars < 40 and largest > 0.2) or (chars == 0 and bool(page.get_drawings()))
            suspect |= text.count("\ufffd") > max(3, len(text) * 0.05)
            suspect |= unreadable(text)
            counts.append(chars)
            if suspect:
                scanned.append(index + 1)
    return {
        "pages": pages,
        "characters": sum(counts),
        "page_characters": counts,
        "ocr_pages": scanned,
        "needs_ocr": bool(scanned) and len(scanned) >= OCR_PAGE_SHARE * len(pages),
    }


def unreadable(text: str) -> bool:
    """Subset fonts without ToUnicode yield C0 control codes instead of letters.

    Such a layer passes character counts yet carries no words, so the page must be OCRed.
    """
    letters = sum(c.isalpha() for c in text)
    controls = sum(ord(c) < 32 and c not in "\t\n\r\f" for c in text)
    return controls > 20 and controls > letters


def prepared_pdf(source: str, options: dict, folder: Path) -> Path:
    """Normalize encrypted/page-limited input so all tools see exactly the same pages."""
    if not options["password"] and not options["pages"]:
        return Path(source)
    with open_pdf(source, options["password"]) as doc:
        pages = select_pages(options["pages"], len(doc))
        doc.select(pages)
        path = folder / "input.pdf"
        doc.save(path)  # Document.save defaults to PDF_ENCRYPT_NONE, verified in PyMuPDF.
        return path

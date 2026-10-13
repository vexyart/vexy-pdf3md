# Quick start

This page walks through the common tasks. The examples assume `vexy-pdf3md` is on
your `PATH`. From a checkout, prefix each command with `uv run`.

## Convert one PDF

1. Run the tool on the file:

    ```bash
    vexy-pdf3md book.pdf
    ```

2. Read the JSON report on stdout. `"ok": true` means the conversion succeeded or was
   skipped.

Result: `book.md` is written beside `book.pdf`.

If `book.md` already exists, the file is skipped and reported with
`"status": "skipped"`. Add `--overwrite=True` to replace it.

## Choose the output file

```bash
vexy-pdf3md book.pdf --output results/renamed.md
```

Result: `results/renamed.md`. For a single input file, `--output` may also be an
existing folder; the file is then written as `FOLDER/book.md`.

## Convert a folder tree

```bash
vexy-pdf3md ./pdfs --output ./markdown --workers=4
```

The tool finds every file ending in `.pdf` (any letter case) under `./pdfs`, and
writes each Markdown file to the same relative path under `./markdown`:

```text
pdfs/part/book.PDF  ->  markdown/part/book.md
```

Up to four PDFs are converted at the same time. Omit `--output` to write each
Markdown file next to its PDF.

## Export images

```bash
vexy-pdf3md book.pdf --media
```

Result:

```text
book.md
book/page-0001-001.png
book/.vexy-pdf3md
```

`book.md` ends with a `## Media` section that links each PNG. Use `--media=pages` to
render whole pages, including vector artwork, instead of only raster images. See
[Output layout and media](output.md).

## Compare converters

```bash
vexy-pdf3md book.pdf --strategies=markit,pymupdf
```

Result: `book.markit.md` and `book.pymupdf.md`, one per strategy. Use
`--strategies=all` to run all five. Add `--fallback=False` when you want each file
to come only from the named converter.

## Convert a scan

```bash
vexy-pdf3md scan.pdf --strategies=tesseract --pages=1-3,5 --lang=pl,en --dpi=200
```

This OCRs pages 1, 2, 3 and 5 with Tesseract, using Polish and English models, at
200 dpi. In automatic mode you usually do not need `--strategies`: a PDF whose pages
look scanned is routed to an OCR converter. See
[Strategies and fallback](strategies.md).

## Use the Python API

```python
from vexy_pdf3md import convert

batch = convert("pdfs", "markdown", strategies="auto", media=True, workers=4)
print(batch.ok)
for item in batch.results:
    print(item.input, item.output, item.status, item.strategy)
```

See [Python API](api.md).

## Run the bundled example

From a checkout:

```bash
uv run examples/smoke.py
```

The script creates a one-page PDF in a temporary folder, converts it with
`strategies="pymupdf"` and `media="pages"`, and checks that the text and the page
image were written. It prints:

```text
Verified nested/example.md and its rendered page image.
```

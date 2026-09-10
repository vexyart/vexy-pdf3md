---
this_file: ANALYSIS.md
---
# Source analysis and design decisions

Inspected 2026-09-10. The source projects are references, not runtime dependencies.

## vexy-paraltext

Source: `../vexy-paraltext/src/vexy_paraltext/convert.py`, `ocr.py`,
`scripts/bake_pdf.py`, `AGENTS.md`, and `WORK.md`.

- `pdf_to_markdown` selects markit for text-layer PDFs and Docling for scans.
  The project's measured bake-off favored markit for column-aware text extraction;
  timings are historical measurements of particular books, not package benchmarks.
- `pymupdf_text` provides a useful independent baseline. `pdf_to_markdown` rejects
  markit output shorter than half that baseline. This catches a successful command
  that silently drops most of a book.
- `ocr_pdf_isolated` exists because Docling crashed natively on some scans.
  A Python exception handler alone cannot catch a segmentation fault.
- `fix_mojibake` is explicitly language-sensitive. Guessing a source encoding can
  corrupt legitimate text, so this package detects conspicuous replacement-character
  corruption but does not copy automatic cp1251 recoding.
- Conversion inside the alignment pipeline is tied to edition folders, EPUB/DjVu
  handling, and cached Markdown. Those assumptions do not belong in a general PDF CLI.

Retained: fast text-first conversion, length checks, and child-process OCR.
Changed: missing markit now permits another installed strategy; all native PDF work,
including inspection and media rendering, runs in child processes. Every selected
page is inspected so a text cover cannot conceal a scanned interior.

Baseline verification: `uv run pytest -q` passed 106 tests, 91.47% coverage.

## pdf22md

Source: `../../github.twardoch/pub/pdf22md/pdf22md/Sources/`:

- `PDF22MDCli/PDF22MDCommand.swift` defines the actual input/output, assets,
  DPI, language, password, fast-mode, and batch arguments. Live installed CLI help
  was checked as well; the new adapter uses single-file conversion.
- `PDF22MD/PDFPageProcessor.swift::processPageEnhanced` runs Vision unless fast
  mode is enabled. Vision failures are suppressed with `try?`; the presence of a
  successful process exit alone therefore does not prove complete OCR.
- `PDFMarkdownConverter.swift::convertEnhanced` gathers page results concurrently
  then restores page order. It can optionally invoke AI correction; this package
  does not enable AI or send content to remote APIs.
- `FontStatistics.swift::analyze` identifies body size by frequency and headings by
  the ranks of retained font sizes. The native Python fallback uses character-weighted
  body size and only larger fonts for headings, avoiding small footnotes as headings.
- `MarkdownGenerator.swift` and `AssetExtractor.swift` place images in Markdown.
  Asset paths can be absolute when an absolute assets directory is provided.
  The Python package instead owns relative links independently of the backend.
- Raster and vector extraction exist in separate Swift modules. The common Python
  media interface exports displayed raster regions (`images`) or rendered full pages
  (`pages`), which include vector graphics. These are rendered PNGs, not original
  compressed image streams or editable vector objects.

Baseline verification: `swift test` passed 90 tests. pdf22md remains an external,
macOS-only executable; it is not bundled in the Python wheel.

## Current APIs and package choices

- [Python Fire guide](https://google.github.io/python-fire/guide/): expose one function
  so `--input` works without a required subcommand. Fire's documented
  [SetParseFn decorator](https://github.com/google/python-fire/blob/master/fire/decorators.py)
  preserves string options, including comma-separated pages and numeric passwords.
  The Python API accepts strategy strings or sequences.
- [PyMuPDF multiprocessing guidance](https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html):
  PyMuPDF must not run concurrently in threads. Threads here only supervise isolated
  Python subprocesses; documents never cross the process boundary.
- [PyMuPDF Page API](https://pymupdf.readthedocs.io/en/latest/page.html): text blocks,
  image-placement bounding boxes, and clipped pixmap rendering. Installed API source
  verified for encryption removal and dictionary/text extraction flags.
- [markit upstream](https://github.com/shift-labs-ai/markit): the installed `markit`
  supports `-q --no-images`; checked via `markit --help`. Package names have varied
  between upstream revisions, so installation instructions point to the upstream repo.
- [Tesseract CLI reference](https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc):
  `tesseract IMAGE stdout -l eng+pol`; installed languages are the operator's choice.
- [Docling pipeline options](https://docling-project.github.io/docling/reference/pipeline_options/):
  current `TesseractCliOcrOptions` uses `mode=OcrMode.FULL_PAGE`; the older
  `force_full_page_ocr` constructor keyword is deprecated. Minimum version 2.126
  reflects the API actually tested. Complete status is required before exporting.

Parsing, OCR, PDF rendering, CLI parsing, and package versions reuse maintained tools.
Custom code is limited to the requested batch/path policy, strategy selection,
quality checks, isolated execution, and artifact publication.

## Routing and failure contract

| Input / option | Ordered automatic candidates, installed tools only |
| --- | --- |
| Text-layer PDF | markit, pymupdf, pdf22md, tesseract, docling |
| Suspected scan or `ocr=always` | pdf22md, tesseract, docling |
| `ocr=never` | text order without tesseract; pdf22md fast, Docling OCR off |

An explicit strategy is attempted first even if unavailable, then eligible automatic
alternatives. `fallback=False` limits each output to its first candidate.
Comma-separated strategies create independent jobs with stable requested-strategy
suffixes; result JSON names the actual winner. Identical fallback outputs are possible
and intentional. This mode compares strategies; it does not select a global winner.

Failures include absent executables, nonzero exit, worker crash, deadline expiry,
unreadable/encrypted PDF, empty text, visible replacement-character corruption,
and retention below `min_text_ratio`. Each attempted backend has a duration and error.
Media is appended only after text passes quality checks.

## Deliberate limits

- Scan detection is heuristic: low text plus substantial raster content, textless
  drawings, or replacement characters. Some mixed-content layouts require `ocr=always`.
- Character retention detects large omissions, not semantic correctness, reading order,
  translation, or omissions limited to individual scanned pages. OCR is not guaranteed
  to recover handwriting or poor scans. Docling checks its complete status, but native
  engines may still produce plausible partial text.
- PyMuPDF fallback is basic block Markdown; complex tables/formulae are better suited
  to Docling. Media is appended in page order rather than interleaved with paragraphs.
- Page selection prepares a decrypted temporary PDF when necessary. Scratch is removed
  on ordinary success/failure/cancellation; forcible host termination can leave scratch.
- Timeouts are per operation, not a whole-batch deadline. POSIX timeout/cancellation
  kills the worker process group; Windows terminates the direct worker only.
- Concurrent jobs within one invocation have collision-checked destinations. Separate
  invocations must not overwrite the same destination concurrently.
- Existing Markdown is skipped without revalidating its provenance. `overwrite=True`
  replaces media only when the folder contains this package's ownership marker.
  Do not put curated files inside generated media folders that will be overwritten.

---
this_file: README.md
---
# vexy-pdf3md

**Documentation:** https://vexy.dev/vexy-pdf3md/

Convert one PDF or an entire folder tree to Markdown. Choose a converter, let the
package select one, or run several strategies side by side. Failed conversions try
another eligible tool; results record every attempt and the actual winner.

## Install

```bash
uv sync
uv run vexy-pdf3md --help
# Install this checkout as a CLI available outside the repository:
uv tool install .
```

Python 3.12+ is required. PyMuPDF provides a working text-layer backend immediately.
Optional tools are discovered on PATH:

- **markit**: install from [upstream instructions](https://github.com/shift-labs-ai/markit).
  Preferred for fast text-layer conversion and multi-column layouts.
- **pdf22md**: build/install [pdf22md](https://github.com/twardoch/pdf22md) on macOS
  for PDFKit extraction and Apple Vision OCR.
- **Tesseract**: `brew install tesseract` on macOS; install the corresponding package
  on other systems. Language models named by `--lang` that are missing from the
  system tessdata are downloaded from tessdata_fast into `~/.cache/vexy-pdf3md/tessdata`
  on first use (`brew install tesseract-lang` works offline instead).
- **Docling**: `uv sync --extra docling`, then use `uv run --extra docling ...`.
  The adapter uses Tesseract for OCR and may download layout/table models on first use.
  For an installed CLI, use `uv tool install '.[docling]'` from this checkout.

## Convert

```bash
# book.pdf -> book.md, beside the PDF
uv run vexy-pdf3md --input book.pdf

# Explicit output file, with images in ./results/renamed/
uv run vexy-pdf3md --input book.pdf --output results/renamed.md --media

# Recursively map PDFs to Markdown, preserving relative subfolders
uv run vexy-pdf3md --input ./pdfs --output ./markdown --workers=4

# Omit --output to write Markdown alongside PDFs throughout the input tree
uv run vexy-pdf3md --input ./pdfs

# Run independent strategies concurrently
uv run vexy-pdf3md --input book.pdf --strategies=markit,pymupdf --media

# OCR, selected pages, language hints, and full-page images (including vectors)
uv run vexy-pdf3md --input scan.pdf --strategies=tesseract \
  --pages=1-3,5 --lang=pl,en --media=pages --dpi=200

# Every strategy side by side
uv run vexy-pdf3md --input scan.pdf --strategies=all --lang=pl,en

# Use Docling for layout/table reconstruction
uv run --extra docling vexy-pdf3md --input book.pdf --strategies=docling
```

`pdf3md` and `python -m vexy_pdf3md` expose the same Fire CLI. Single-file input
accepts an explicit `.md` filename or an existing output directory. Directory input
always treats `--output` as a directory, even if its name ends in `.md`.

## Output contract

```text
pdfs/part/book.PDF
  --output markdown
    -> markdown/part/book.md
  --output markdown --strategies=markit,pymupdf --media
    -> markdown/part/book.markit.md
       markdown/part/book.markit/page-0001-001.png
    -> markdown/part/book.pymupdf.md
       markdown/part/book.pymupdf/page-0001-001.png
```

Suffixes are added only when multiple strategies are requested. They identify the
requested strategy, even if a fallback produces that output; JSON reports identify
the actual backend. Use `--fallback=False` for strict backend comparisons.

`--media` / `--media=images` exports displayed raster-image regions as PNGs, appended
under a Media heading in page order. `--media=pages` renders each complete selected
page, including vector artwork. Media links are relative and URL-escaped. Original
embedded image formats, editable vectors, and exact inline placement are not preserved.
The media directory uses the complete Markdown stem and is created even if no images
are found; `.vexy-pdf3md` marks it as generated.

Existing Markdown is **skipped by default**. `--overwrite=True` replaces it only after
conversion passes quality checks. Existing media directories are replaceable only if
they carry this package's ownership marker. Keep curated files outside generated media
directories. Case-insensitive destination collisions are rejected before processing.
Directory symlinks are not followed and PDF symlinks within trees are skipped; an
explicit single-file symlink is resolved to its target.

## Selection and fallback

- Text-layer PDFs: **markit → pymupdf → pdf22md → tesseract → docling**.
- Suspected scanned/mixed PDFs: **pdf22md → tesseract → docling**. A page counts as
  scanned when it is mostly image, or when its text layer is unreadable control codes
  (subset fonts without a ToUnicode map).
- Only installed candidates participate in automatic selection. An explicitly named
  missing backend produces a failed attempt before fallback.
- Native crashes, timeout, nonzero exit, empty output, replacement-character corruption,
  and substantial text loss trigger fallback. The default retention threshold is 50%
  of the PDF's alphanumeric text layer, before media is appended.
- All selected pages are inspected. A document is routed to OCR only when at least
  20% of the selected pages look scanned; a lone screenshot page in a long text document
  produces a warning instead. Detection and length checks are heuristics; they cannot
  prove complete or correct OCR. Use `--ocr=always` when automatic routing misses
  scanned content. `--ocr=never` deliberately permits text-layer-only extraction.
- With several strategies requested, a failed strategy never falls back to one of its
  siblings: those already get their own output, so the file would be a duplicate under
  a misleading suffix. A warning names the actual backend whenever it differs.

PyMuPDF's basic fallback preserves text blocks and infers larger-font headings.
It does not reconstruct sophisticated tables. For difficult layouts, compare outputs
or request Docling. Image-only documents still require usable OCR text: exporting page
images alone does not count as successful Markdown conversion.

## Engine comparison

Measured on 123 Microsoft localization style guides (text-layer PDFs, 30–100 pages,
59 in non-Latin scripts), each converted with every strategy. Only English OCR models
were installed, so OCR ratings cover text-layer input, not scans.

| Strategy | Rating | Observed |
| --- | --- | --- |
| markit | ★★★★☆ default | Tables, reflowed paragraphs, running headers/footers dropped. Loses 4–22% of Greek and Indic letters (conjuncts, pre-base vowels), joins hyphenated words, shows `312x90pt` image placeholders, may emit U+FFFD for fonts without Unicode maps. |
| pymupdf | ★★★☆☆ most complete text | Keeps every mapped glyph, font-size headings, page footers, and hard line breaks. No tables. Missed inline Cyrillic runs in one Serbian guide that markit recovered. |
| pdf22md | ★★☆☆☆ | Text equals PyMuPDF's layer, but one line per text run, no headings or tables, footers kept. Vision OCR turned Cyrillic into Latin lookalikes when routing forced OCR. |
| tesseract | ★☆☆☆☆ on text PDFs | About 5% of words lost and 8% garbage on Latin scripts; non-Latin scripts unreadable without language packs. Only for real scans. |
| docling | not rated | Not installed during the run: all 123 `.docling.md` files were byte-identical markit fallbacks, which prompted the sibling-fallback rule above. |

Best choice per guide: markit for 110 documents, PyMuPDF for the Greek and ten Indic
guides where markit dropped script letters, and for two Bengali/Konkani guides whose
fonts lack Unicode maps. One Kyrgyz guide was misrouted to OCR by a single screenshot
page; the page-share threshold above fixes that.

## Options

| Option | Default | Meaning |
| --- | --- | --- |
| `--strategies` | `auto` | One tool, `all`, or comma-separated independent variants |
| `--workers` | `2` | Maximum simultaneous isolated jobs, 1–64 |
| `--timeout` | `600` | Seconds per inspection, backend attempt, or media export |
| `--fallback` | `True` | Try alternative eligible converters |
| `--media` | `False` | `True`/`images`, `pages`, or `False`/`none` |
| `--overwrite` | `False` | Replace Markdown and owned generated media |
| `--pages` | all | One-based ranges, e.g. `1-3,5`, sorted and deduplicated |
| `--password` | empty | Password for encrypted PDFs; omitted from reports |
| `--ocr` | `auto` | `auto`, `always`, or `never` |
| `--lang` | `eng` | OCR language hints as ISO 639-1 or Tesseract codes, e.g. `pl,en` or `pol+eng`; shared by Tesseract, Docling, and pdf22md Vision |
| `--dpi` | `150` | OCR and media resolution, 72–600 |
| `--min-text-ratio` | `0.5` | Minimum retained text-layer fraction, 0–1 |
| `--verbose` | `False` | Backend diagnostics on stderr |

Timeouts apply per operation, so fallback can extend total time. POSIX timeout and
Ctrl-C terminate the worker process group, including converter subprocesses. On Windows
only the direct worker is terminated. Separate invocations should not overwrite the
same destinations concurrently.

## Python API and exit codes

```python
from vexy_pdf3md import convert

batch = convert("pdfs", "markdown", strategies="auto", media=True, workers=4)
for item in batch.results:
    print(item.input, item.output, item.status, item.strategy)
    for attempt in item.attempts:
        print(attempt.strategy, attempt.status, attempt.error)
assert batch.ok
```

The CLI prints a JSON batch report to stdout. Exit status **0** means every output
succeeded or was skipped, **1** means at least one conversion failed, and **2** means
invalid configuration/input arguments. A bad PDF does not stop other jobs. API argument
and path errors raise; individual document failures are returned in `BatchResult`.
No cloud OCR or AI service is invoked by this package.

## Develop

```bash
./test.sh                                    # lint, types, 80% coverage gate, smoke
uv run --extra docling pytest -m optional    # real Docling + model integration
uvx hatch test                              # isolated package test environment
uv build                                    # Git-derived version, wheel and sdist
./build.sh docs                             # strict documentation build into docs/
```

The docs build uses Python 3.13 and fly-january 0.4.0 or later (remote theme assets) with
`extra.fly.chrome` set to `none` in `src_docs/mkdocs.yml`.

## Publish

```bash
./build.sh package    # clean dist/, uv build, twine check
./publish.sh          # request the next patch release through GitHub Actions
```

`hatch-vcs` derives versions from Git tags and generates the gitignored
`src/vexy_pdf3md/__version__.py` during builds/installs. Rebuild or reinstall after
changing tags to refresh editable-install versions; never commit the generated file.

Run `./test.sh` and push the release commit to the default branch before running
`./publish.sh`. The script uses the authenticated GitHub CLI to dispatch
`release.yml`. GitHub Actions builds the tagged source, attaches the wheel and
sdist to the GitHub release, and uploads them to PyPI through Trusted Publishing.

See [ANALYSIS.md](ANALYSIS.md) for both source-project investigations and routing
tradeoffs, [DEPENDENCIES.md](DEPENDENCIES.md) for dependency roles/licenses, and
[WORK.md](WORK.md) for verification evidence. The package's own code is Apache-2.0;
dependencies have their own licenses, including PyMuPDF's AGPL/commercial terms.

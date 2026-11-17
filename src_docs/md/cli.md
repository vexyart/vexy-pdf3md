---
this_file: src_docs/md/cli.md
tags: [Command line]
---

# Command line

## Synopsis

```bash
vexy-pdf3md INPUT [--output=OUTPUT] [--strategies=auto] [--media=False] [options]
```

`pdf3md` and `python -m vexy_pdf3md` accept the same arguments. The CLI is built
with [Python Fire](https://github.com/google/python-fire), so:

- `INPUT` can be given as the first positional argument or as `--input=INPUT`.
- Options accept both `--name=value` and `--name value`.
- Option names with underscores also accept hyphens: `--min_text_ratio` and
  `--min-text-ratio` are the same option.
- `vexy-pdf3md --help` prints the full option list.

## Arguments and options

| Option | Short | Default | Meaning |
| --- | --- | --- | --- |
| `INPUT` / `--input` | | required | PDF file, or folder searched recursively for `.pdf` files (any case) |
| `--output` | | beside the input | Markdown file or output folder |
| `--strategies` | `-s` | `auto` | `auto`, `all`, or comma-separated names from `markit,pymupdf,pdf22md,tesseract,docling` |
| `--media` | | `False` | `True` or `images`: export raster images. `pages`: render whole pages. `False` or `none`: no media |
| `--workers` | `-w` | `2` | Maximum simultaneous jobs, 1 to 64 |
| `--timeout` | `-t` | `600` | Seconds allowed for each inspection, converter attempt, or media export |
| `--fallback` | `-f` | `True` | Try another converter after a failure |
| `--overwrite` | | `False` | Replace existing Markdown and media folders this package created |
| `--pages` | | all pages | One-based, inclusive page selection, for example `1-3,5` |
| `--password` | | empty | Password for encrypted PDFs. Never written to reports or logs |
| `--lang` | `-l` | `eng` | OCR language hints as ISO 639-1 or Tesseract codes, for example `pl,en` or `pol+eng` |
| `--dpi` | `-d` | `150` | Resolution for OCR and media rendering, 72 to 600 |
| `--ocr` | | `auto` | `auto` detects scans, `always` requires OCR, `never` uses text layers only |
| `--min_text_ratio` | | `0.5` | Minimum share of the PDF's text layer the output must keep, 0 to 1 |
| `--verbose` | `-v` | `False` | Print converter diagnostics to stderr |

## Option details

### `--strategies`

- `auto` lets the package rank the installed converters. See
  [Strategies and fallback](strategies.md).
- A single name, such as `--strategies=pymupdf`, tries that converter first.
- Several names, such as `--strategies=markit,pymupdf`, run each converter as an
  independent job and add a `.STRATEGY.md` suffix to each output file.
- `all` is shorthand for all five names.
- `auto` cannot be combined with other names, and a name cannot appear twice.

### `--pages`

Pages are numbered from 1. Ranges are inclusive. The selection is sorted and
duplicates are removed, so `5,1-3,2` selects pages 1, 2, 3 and 5. A range outside the
document, such as `1-90` on a 40-page PDF, fails that document with
`page range '1-90' is outside 1-40`.

When `--pages` or `--password` is used, the tool first writes a temporary, unencrypted
copy containing only the selected pages, so every converter sees exactly the same
pages.

### `--lang`

Give one list for all OCR converters. Each entry may be an ISO 639-1 code (`pl`,
`en`, `zh-hant`) or a Tesseract model name (`pol`, `eng`, `chi_tra`). Entries may be
separated by commas or `+`. The list is mapped to:

- Tesseract `-l` codes, for example `pl,en` becomes `pol+eng`;
- Docling's Tesseract OCR options;
- pdf22md `--languages` codes for Apple Vision, for example `pol,eng` becomes `pl,en`.

Unknown codes are passed through unchanged, so any installed Tesseract model can be
named.

### `--media`

| Value | Result |
| --- | --- |
| `False`, `none` | No media folder |
| `True`, `images` | Each displayed raster image region is rendered to PNG |
| `pages` | Each selected page is rendered to PNG, including vector artwork |

See [Output layout and media](output.md).

### `--ocr`

- `auto`: every selected page is inspected. The document is sent to OCR converters
  only when at least 20% of the selected pages look scanned.
- `always`: only OCR converters (`pdf22md`, `tesseract`, `docling`) are used.
- `never`: `tesseract` is removed from the candidates, and Docling runs with OCR
  turned off. pdf22md runs in its `--fast` mode, without Vision OCR.

### `--timeout`

The limit applies to each operation separately: the inspection, each converter
attempt, and the media export. A fallback chain can therefore take longer in total
than one timeout.

## Output and exit status

The CLI prints a JSON batch report to stdout. Diagnostics go to stderr.

| Exit status | Meaning |
| --- | --- |
| `0` | Every output succeeded or was skipped |
| `1` | At least one conversion failed |
| `2` | Invalid options or input path; nothing was converted |

For exit status `2`, the report is a single line with the error:

```bash
$ vexy-pdf3md book.pdf --workers=0
{"ok": false, "error": "workers must be an integer from 1 to 64"}
```

A PDF that fails to convert does not stop the other jobs in the batch.

## Examples

```bash
# book.pdf -> book.md, beside the PDF
vexy-pdf3md book.pdf

# Explicit output file, with images in ./results/renamed/
vexy-pdf3md book.pdf --output results/renamed.md --media

# Map a tree of PDFs to a tree of Markdown files
vexy-pdf3md ./pdfs --output ./markdown --workers=4

# Run two converters side by side, with images
vexy-pdf3md book.pdf --strategies=markit,pymupdf --media

# OCR selected pages with Polish and English hints, full-page images
vexy-pdf3md scan.pdf --strategies=tesseract --pages=1-3,5 --lang=pl,en --media=pages --dpi=200

# Every converter side by side
vexy-pdf3md scan.pdf --strategies=all --lang=pl,en

# Docling, from a checkout
uv run --extra docling vexy-pdf3md book.pdf --strategies=docling
```

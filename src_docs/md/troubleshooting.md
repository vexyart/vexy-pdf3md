# Troubleshooting

Start with `--verbose`. It prints each converter failure to stderr. The JSON report
also lists every attempt with its error.

## The file was skipped

```json
"status": "skipped"
```

The Markdown file already exists. Add `--overwrite=True` to replace it.

## `media directory already exists and is not replaceable`

A folder with the Markdown file's stem already exists, and either `--overwrite` is not
set or the folder has no `.vexy-pdf3md` marker. The tool does not delete folders it
did not create. Move or rename the folder, then run again.

## `scanned PDF needs an OCR tool`

At least 20% of the selected pages look scanned, and none of `pdf22md`, `tesseract` or
Docling is installed. Install one of them (see [Installation](installation.md)).
If the document does have a usable text layer, run with `--ocr=never`.

## `document needs OCR; this strategy only reads the text layer`

You named `markit` or `pymupdf`, but the document was classified as scanned (or you
passed `--ocr=always`). The attempt fails and fallback moves on to OCR converters.
To force text-layer extraction, add `--ocr=never`.

## A scanned page was not OCRed

The log shows:

```text
book.pdf: pages [12] look scanned but the text layer is used; pass --ocr=always to OCR the whole document
```

Fewer than 20% of the selected pages looked scanned, so the text layer was used.
Run again with `--ocr=always`, or use `--pages` to convert only the scanned part.

## `truncated output: N characters vs M in text layer`

The converter kept fewer than `--min_text_ratio` (default `0.5`) of the letters and
digits in the PDF's text layer. The next converter is tried. If you know the text
layer contains material you do not need (for example hidden text), lower the ratio:

```bash
vexy-pdf3md book.pdf --min-text-ratio=0.3
```

## `text layer is unreadable control codes`

The PDF uses subset fonts without a ToUnicode map. The text layer has characters but
no words. Such pages are classified as scanned; install an OCR converter so they can
be OCRed.

## `converter returned replacement-character corruption`

The output contains too many `U+FFFD` characters (more than 2%), usually from fonts
without Unicode maps. Try another strategy, for example `--strategies=pymupdf`, or an
OCR strategy.

## `markit is not installed or not on PATH`

The named external converter was not found. Check with `which markit`. The same
message appears for `pdf22md` and `tesseract`. For Docling the message is
`docling is not installed; install vexy-pdf3md[docling]`.

## `no Tesseract model for 'xyz' and download failed`

The language model named by `--lang` is not installed and could not be downloaded
from `tessdata_fast`. Check the code (for example `pol`, not `pl-PL`), your network,
or install the language pack locally. On macOS: `brew install tesseract-lang`.

## `PDF needs a valid password`

The PDF is encrypted. Pass `--password=...`. The password is never written to the
JSON report or logs; it appears as `[redacted]` in error messages.

## `page range '1-90' is outside 1-40`

`--pages` names pages beyond the end of the document. Page numbers start at 1.

## `output collision: PATH`

Two jobs would write the same file, compared case-insensitively, or an output would
overwrite an input PDF. Rename one of the PDFs, or write to a different `--output`.

## The output file name has the wrong converter's suffix

With several strategies, the suffix names the strategy you requested. If that
converter failed, another one may have written the file; a warning names it and the
report's `strategy` field records it. Use `--fallback=False` to prevent this.

## A run takes much longer than `--timeout`

`--timeout` applies to each operation: the inspection, each converter attempt, and the
media export. A document that falls back through several converters can take several
timeouts.

# Strategies and fallback

This page explains how `vexy-pdf3md` picks a converter, when it rejects a result,
and what happens next.

## Step 1: inspect the PDF

Before any conversion, a worker process opens the PDF with PyMuPDF and checks every
selected page. A page is marked as *looks scanned* when any of these is true:

- it has fewer than 40 letters or digits in its text layer and an image covers more
  than 20% of the page;
- it has no text at all but contains vector drawings;
- more than 5% of its text (and more than 3 characters) is the replacement character
  `U+FFFD`;
- its text layer is mostly control codes. This happens with subset fonts that have no
  ToUnicode map: the text layer has characters but no readable words.

The document *needs OCR* only when at least 20% of the selected pages look scanned.
If some pages look scanned but fewer than 20%, the tool logs a warning naming those
pages and uses the text layer. Pass `--ocr=always` to OCR such a document anyway.

## Step 2: rank the candidates

The candidate order depends on whether the document needs OCR:

| Document | Order |
| --- | --- |
| Text layer | `markit` → `pymupdf` → `pdf22md` → `tesseract` → `docling` |
| Needs OCR, or `--ocr=always` | `pdf22md` → `tesseract` → `docling` |

With `--ocr=never`, `tesseract` is removed from the list.

### `--strategies=auto`

Only installed converters are kept, in the order above. `pymupdf` is always
installed. If a scanned document has no installed OCR converter, the document fails
with:

```text
scanned PDF needs an OCR tool: install pdf22md, Tesseract, or vexy-pdf3md[docling]
```

### A named strategy

The named converter is tried first, even if it is not installed (the attempt then
fails with `markit is not installed or not on PATH`, or similar). The installed
converters from the ranked list follow as fallbacks.

### Several named strategies

Each named converter gets its own job and its own output file. A failed job never
falls back to one of its siblings, because that sibling already writes its own file
and the fallback would only produce a duplicate under a misleading suffix. Fallback
goes to converters you did not name.

### `--fallback=False`

Only the first candidate is tried. Use this for strict comparisons between
converters.

## Step 3: convert and check the result

Each attempt runs in a separate worker process. An attempt fails when:

- the worker crashes, exits with a nonzero status, or exceeds `--timeout`;
- an external converter exits with a nonzero status;
- the document needs OCR and the converter only reads the text layer
  (`markit`, `pymupdf`);
- the converter is `tesseract` and `--ocr=never` is set;
- the output has no letters or digits;
- the output is mostly control codes;
- more than 2% of the output (and more than 3 characters) is `U+FFFD`;
- the output keeps fewer letters and digits than `--min_text_ratio` times the count in
  the PDF's text layer (default: half).

The text checks ignore HTML comments and Markdown image links, and they run before
media is appended.

When an attempt fails, its error is recorded in `attempts` and the next candidate is
tried. When every candidate fails, the result has `"status": "failed"` and
`"error": "all conversion strategies failed"`.

If the converter that succeeded is not the one you named, a warning is printed:

```text
book.pdf: markit failed; pymupdf wrote /path/to/book.markit.md
```

## What each converter does

### markit

Runs `markit -q --no-images FILE.pdf` and reads stdout.

### pymupdf

Built in. Extracts text blocks page by page. The most common font size (weighted by
characters) is treated as body text. Up to six larger sizes (more than 15% above body
size) become heading levels `#` to `######`. Pages are separated by `---`. It does not
reconstruct tables.

### pdf22md

Runs `pdf22md --input FILE --output native.md --quiet --languages CODES --dpi DPI`.
`--fast` is added when OCR is not needed or `--ocr=never` is set.

### tesseract

Renders each page to PNG at `--dpi` and runs
`tesseract PAGE.png stdout -l CODES --tessdata-dir DIR` on it. Pages are separated by
`---`. Missing language models are downloaded on first use (see
[Installation](installation.md#tesseract)).

### docling

Runs Docling's `DocumentConverter` with OCR enabled unless `--ocr=never`. When
`tesseract` is on `PATH`, Docling uses Tesseract with the `--lang` codes, at a scale
of `--dpi` / 72. For documents that need OCR, or with `--ocr=always`, it OCRs whole
pages; otherwise only bitmap regions.

## Limits

Scan detection and length checks are heuristics. They cannot prove that OCR is
complete or correct. Exporting page images does not count as a successful
conversion: an image-only document still needs usable OCR text.

## Measured comparison

The project measured all five strategies on 123 Microsoft localization style guides:
text-layer PDFs of 30 to 100 pages, 59 of them in non-Latin scripts. Only English OCR
models were installed, so the OCR ratings describe text-layer input, not scans.

| Strategy | Observed |
| --- | --- |
| `markit` | Default choice. Keeps tables, reflows paragraphs, drops running headers and footers. Lost 4–22% of Greek and Indic letters (conjuncts, pre-base vowels), joins hyphenated words, shows `312x90pt` image placeholders, may emit `U+FFFD` for fonts without Unicode maps. |
| `pymupdf` | Most complete text. Keeps every mapped glyph, font-size headings, page footers and hard line breaks. No tables. Missed inline Cyrillic runs in one Serbian guide that markit recovered. |
| `pdf22md` | Same text as the PyMuPDF layer, but one line per text run, no headings or tables, footers kept. When routing forced OCR, Vision turned Cyrillic into Latin lookalikes. |
| `tesseract` | On text PDFs, about 5% of words lost and 8% garbage on Latin scripts; non-Latin scripts unreadable without language packs. Use it for real scans. |
| `docling` | Not rated: it was not installed during the run, so every `.docling.md` file was a markit fallback. This result led to the no-sibling-fallback rule above. |

markit gave the best result for 110 documents. PyMuPDF was better for the Greek guide
and ten Indic guides where markit dropped letters, and for two Bengali and Konkani
guides whose fonts lack Unicode maps. One Kyrgyz guide was sent to OCR because of a
single screenshot page; the 20% page-share threshold now prevents that.

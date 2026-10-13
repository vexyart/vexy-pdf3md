# Changelog

Release versions come from Git tags (`v1.0.0` to `v1.0.4` so far). The full history
is in [`CHANGELOG.md`](https://github.com/vexyart/vexy-pdf3md/blob/main/CHANGELOG.md)
and the [Git log](https://github.com/vexyart/vexy-pdf3md/commits/main).

## Unreleased

### Documentation and packaging

- Documentation site built from `src_docs/md/` with ProperDocs and MaterialX,
  published at <https://vexy.dev/vexy-pdf3md/>.
- `build.sh` builds the documentation and the package; `publish.sh` tags with
  gitnextver, builds and uploads with `uv publish`.

### Conversion

- Text layers made of control codes (subset fonts without ToUnicode) are detected as
  scanned pages. Text-layer converters' output of this kind is rejected, and Docling
  runs in full-page OCR mode for such documents.
- `--strategies=all` runs every strategy side by side.
- `--language` and `--vision-languages` are replaced by one `--lang` list (`pl,en` or
  `pol+eng`) used by Tesseract, Docling and pdf22md Vision.
- Missing Tesseract models are downloaded from `tessdata_fast` into
  `~/.cache/vexy-pdf3md/tessdata`. Output configs are mirrored there so Docling's TSV
  parsing still works with `--tessdata-dir`. Parallel workers stage downloads in
  separate files.
- Docling: requires pydantic 2.12 or later, and a `torchaudio` build that fails to
  load is replaced by a stub.
- A document is routed to OCR only when at least 20% of the selected pages look
  scanned. Isolated image pages log a warning instead.
- A failed strategy in a multi-strategy run no longer falls back to a sibling
  strategy. A warning names the converter whenever it differs from the requested one.
- New `all` extra.

### Initial release

- Fire CLI (`vexy-pdf3md`, `pdf3md`, `python -m vexy_pdf3md`) and Python API.
- Single-file and recursive-tree conversion, strategy suffixes, and generated media
  folders with relative links.
- Adapters for markit, PyMuPDF, pdf22md, Tesseract and optional Docling.
- Scan-aware routing, fallback, text-retention checks, operation timeouts,
  native-crash isolation, bounded concurrency and per-attempt JSON reports.
- Page selection, passwords, OCR controls and languages, DPI and overwrite policy.
- Staged publication, collision detection, media ownership checks, and preservation
  of previous output when publication fails.

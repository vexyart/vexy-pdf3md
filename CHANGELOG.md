---
this_file: CHANGELOG.md
---
# Changelog

## Unreleased

- Generate and import gitignored `__version__.py` with the hatch-vcs build hook.
- Add `publish.sh`: validate, clean generated dirt, commit/tag via `uvx gitnextver`,
  verify pushes, build fresh tagged artifacts, and upload with `uv publish`.
- Add isolated release-flow regression tests and build-before-test version generation.

- Added Fire CLI (`vexy-pdf3md`, `pdf3md`, and `python -m vexy_pdf3md`) and Python API.
- Added single-file and recursive-tree conversion, deterministic basenames, independent
  strategy suffixes, and generated media directories with relative links.
- Added markit, PyMuPDF, pdf22md, Tesseract, and optional Docling adapters.
- Added scan-aware routing, fallbacks, text-retention checks, operation timeouts,
  native-crash isolation, bounded concurrency, and per-attempt JSON evidence.
- Added page selection, passwords, OCR controls/languages, DPI, and overwrite policy.
- Added staged publication, collision detection, generated-media ownership checks,
  and preservation of previous output on ordinary publication failure.
- Added synthetic-PDF regression tests, real OCR integrations, documentation of both
  source projects, and a runnable smoke example.

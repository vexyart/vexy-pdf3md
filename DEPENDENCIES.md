---
this_file: DEPENDENCIES.md
---
# Dependencies

| Dependency | Purpose |
| --- | --- |
| Python >=3.12 | Runtime and standard-library orchestration |
| Fire | Direct `--input` / `--output` CLI from a typed function |
| loguru | Optional backend diagnostic logging |
| PyMuPDF | PDF inspection, native fallback, page selection, raster rendering |
| Docling >=2.126,<3 (extra) | Layout-aware conversion, tables, and OCR |
| markit (external, optional) | Fast, column-aware text-layer conversion |
| pdf22md (external, optional, macOS) | PDFKit extraction and Vision OCR |
| Tesseract (external, optional) | Local OCR; also used by the Docling adapter |
| hatchling / hatch-vcs | Wheel/sdist builds, versions derived from Git tags |
| fly-january 0.3.0 or later (via uvx) | Theme and plugin for the ProperDocs site |
| GitHub CLI (`gh`) | Dispatch the release workflow from `publish.sh` |
| pytest / pytest-cov | Regression/integration tests and subprocess coverage |
| ruff / ty | Formatting, lint, and type checks |

`uv.lock` records resolved Python versions. Core installation needs no model downloads.
Docling can download layout/table models on first use. OCR language data is installed
separately for Tesseract; `tesseract --list-langs` shows what is available.

The repository's Apache-2.0 license covers its own code. Dependencies retain their
respective licenses; PyMuPDF is AGPL/commercial licensed. External executables are
discovered through PATH and are not copied into distribution artifacts.

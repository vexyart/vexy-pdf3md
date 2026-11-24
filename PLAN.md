---
this_file: PLAN.md
---
# Remaining work

- Confirm the PyPI trusted publisher for `vexy-pdf3md`. The project owner must check the GitHub repository `vexyart/vexy-pdf3md`, workflow `release.yml` and environment `pypi` in the project's Publishing settings.
- Recheck native scan OCR on macOS with a working `pdf22md` installation. Run `uv run pytest 'tests/test_strategies.py::test_real_scanned_document_ocr[pdf22md]'` and confirm the scan yields the expected text with fallback disabled.

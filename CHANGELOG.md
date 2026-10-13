---
this_file: CHANGELOG.md
---
# Changelog

## Unreleased

- Add documentation site: `src_docs/md/` (11 pages) built with ProperDocs + MaterialX by
  `src_docs/build.sh` into `docs/`, served at https://vexy.dev/vexy-pdf3md/; `Docs` workflow
  rebuilds it on push to `main`.
- Add `build.sh` (`all|docs|package`). Replace `publish.sh` with the shared gitnextver +
  `./build.sh package` + `uv publish` flow; adapt `tests/test_release.py` to it.
- Add project URLs and classifiers; anchor sdist includes to the repository root.
- Stop tracking `.omc/` session state; ignore `node_modules/` and `site/`.

- Detect text layers made of C0 control codes (subset fonts without ToUnicode, common in
  Polish lab reports) as scanned pages, reject such output from text-layer strategies, and
  run Docling in full-page OCR mode for them.
- Accept `--strategies=all` as shorthand for every strategy run side by side.
- Replace `--language`/`--vision-languages` with one `--lang` hint list (`pl,en` or
  `pol+eng`) mapped onto Tesseract, Docling, and pdf22md Vision codes.
- Download missing Tesseract models from tessdata_fast into `~/.cache/vexy-pdf3md/tessdata`
  and mirror output configs there, so `--tessdata-dir` keeps Docling's TSV parsing intact.
  Downloads and copies stage per-process files, so parallel workers never race.
- Docling: require pydantic 2.12+ (older user-site copies crash pipeline hashing) and
  stub a torchaudio build that fails to load, which transformers imports unconditionally.
- Route a document to OCR only when at least 20% of selected pages look scanned;
  isolated image pages now log a warning instead of forcing whole-document OCR.
- Never fall back to a sibling strategy of one multi-strategy run; warn whenever the
  actual backend differs from the requested suffix.
- Add the `all` extra (`uv pip install -e '.[all]'`) and an engine comparison in README
  measured on 123 localization style guides.

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

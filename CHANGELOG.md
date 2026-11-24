---
this_file: CHANGELOG.md
---
# Changelog

## Unreleased

- The documentation build accepts fly-january 0.3.0 or later.
- Site now uses the fly-january 0.2.1 theme (chrome: none).
- Build the documentation from `src_docs/md/` into `docs/` with `./build.sh docs`. The Docs workflow rebuilds the site on changes to its sources.
- `./build.sh package` builds distributions locally. `./publish.sh` dispatches `release.yml` to build from a tag and publish through PyPI Trusted Publishing (`324c469`).
- The PyPI project owner must retain the GitHub trusted publisher used for 1.0.6 (`vexyart/vexy-pdf3md`, workflow `release.yml`, environment `pypi`). Restore it if missing.
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
- Add isolated release-flow regression tests and build-before-test version generation.

- Added single-file and recursive-tree conversion, deterministic basenames, independent
  strategy suffixes, and generated media directories with relative links.
- Added markit, PyMuPDF, pdf22md, Tesseract, and optional Docling adapters.
- Added scan-aware routing, fallbacks, text-retention checks, operation timeouts,
  native-crash isolation, bounded concurrency, and per-attempt JSON evidence.
- Added page selection, passwords, OCR controls/languages, DPI, and overwrite policy.
- Added staged publication, collision detection, generated-media ownership checks,
  and preservation of previous output on ordinary publication failure.

## 2026-10-18: documentation plugins

- Use MaterialX search, inherited metadata and a topic index; keep ordered navigation in awesome-nav.
- The documentation wrapper installs the plugins required by this site.
- Strict documentation build and rendered output checks passed.

## 2026-09-10 implementation verification

- Documented converter choices in `ANALYSIS.md` after verifying both source baselines (106 vexy-paraltext tests and 90 pdf22md tests passed, `b5a5d70`).
- Defined acceptance tests for conversion, media, failures and CLI behaviour (47 tests passed with 89.30% coverage, `b5a5d70`).
- Implemented the Python API and Fire CLI, including `python -m vexy_pdf3md`. Both installed wheel commands, `vexy-pdf3md` and `pdf3md`, converted a PDF with page images (`b5a5d70`).
- Reviewed the implementation and verified all five backends (54 tests passed with 91.91% coverage, recorded in `WORK.md` at `b5a5d70`).

---
this_file: WORK.md
---
# Work log

The docs build currently pins fly-january 0.2.1.

## 2026-11-24 — documentation theme

- `./build.sh docs` and the Docs workflow both use `src_docs/build.sh` and
  `src_docs/mkdocs.yml`. The strict build with fly-january 0.1.1 exited 0 with
  no warnings. All 13 generated HTML pages use the native header and footer,
  neutral labels and the MaterialX favicon. The five Fly assets match the
  installed wheel. All 842 local link and asset references resolve. Search and
  tags cover all 12 documentation pages.
- `./test.sh` passed Ruff and ty. Pytest reported 68 passed, 5 failed, 1 skipped
  and 1 deselected, with 92.94% coverage. All five failures reproduced against
  the original commit `dcd74fa`. Four release tests mock the previous local
  publishing flow. The installed `pdf22md` exited with signal 5 after resuming
  a Swift continuation twice during its scan test. `uv run examples/smoke.py`
  passed separately.

## Multilingual OCR and Docling repair (2026-09-11)

- Reproduced on a rasterised Polish pangram: Tesseract with the `eng` model garbled every
  diacritic, `--language pol` failed (no `pol.traineddata`), Docling crashed before OCR.
- Docling root causes on this host: a stale user-site pydantic 2.11.7 shadowed the 2.12.5
  Docling was installed against (pipeline-options hash raised "Circular reference"), then
  transformers imported a torchaudio built for an older torch and died in `dlopen`.
  Upgraded the user-site pydantic; stubbed torchaudio in the Docling worker; pinned
  `pydantic>=2.12` in the docling extra.
- Third Docling failure was ours: `--tessdata-dir` also relocates `configs/tsv`, so a bare
  model directory made Tesseract print plain text and Docling's TSV parser hit KeyError.
  The cache now mirrors `configs/` and `tessconfigs/` from the system tessdata.
- New `--lang` (`pl,en` or `pol+eng`) replaces `--language`/`--vision-languages`; codes
  map onto Tesseract, Docling, and Vision. Missing models download from tessdata_fast.
- Real corpus (15 Polish lab reports): 11 carry text layers of C0 control codes, so auto
  routing sent them through markit and produced garbage. Inspection now flags such pages
  as scanned, check_quality rejects such output, Docling uses full-page OCR for them.
  After the fix auto picks pdf22md for all 11; tesseract output has 0.75–0.93 word overlap
  with pdf22md and equal diacritic counts.
- Result: `--strategies=all --lang=pl,en` yields identical correct Polish from tesseract,
  pdf22md, and docling; markit/pymupdf refuse the scan by design. Tests: languages unit
  tests plus real Polish OCR through tesseract and docling.

## Style-guide engine bake-off (2026-09-10)

- Compared 615 outputs of 123 Microsoft style guides across markit, pymupdf, pdf22md,
  tesseract, and docling. Metrics: alphanumeric retention against the PyMuPDF text
  layer, per-script letter counts, U+FFFD, headings, table rows, footer lines, word loss.
- All docling files were byte-identical to markit (Docling absent, silent fallback).
  One Kyrgyz guide had all five outputs identical: page 38 (one screenshot) forced
  whole-document Vision OCR, which lost every Cyrillic letter.
- markit dropped 4–22% of Greek/Indic letters in 11 guides and emitted U+FFFD in two;
  PyMuPDF kept them. PyMuPDF missed inline Cyrillic runs in the Serbian (Bosnia) guide.
- Tesseract (English model only): ~5% words lost, ~8% garbage; never best.
- Code: OCR page-share threshold, no sibling fallback, warnings, `all` extra; tests added.
- Kept one Markdown per guide: markit for 110, PyMuPDF for 13; Kyrgyz regenerated
  from its text layer with the fixed routing.

## Release workflow follow-up

- Verified current hatch-vcs and uv publishing documentation and inspected the installed
  gitnextver 1.0.1 implementation. It commits/tags only when changes exist; a separate
  pre-commit would prevent it from generating a release tag.
- Added failing release-contract tests before implementation (publish.sh absent).
- Configured the hatch-vcs build hook and gitignored generated `__version__.py`;
  package imports it directly. Build/install runs before test collection.
- Added a Bash 3.2-compatible publish flow. It removes only explicitly generated dirt,
  preserves source changes for gitnextver to commit, checks final tree/tag/remote state,
  verifies archive and generated versions, and uploads only fresh artifacts via uv.
- Validation uses frozen dependency resolution so the version-bearing lockfile cannot
  dirty the tagged tree. Type checks explicitly install the optional Docling extra.
- Test publication uses disposable repositories and mocked upload commands; the live
  package checkout is neither committed/tagged nor pushed/uploaded by this task.
- Seven isolated release-contract tests pass, including rejected remote push,
  absent tag, mismatched artifact version, failing tests/upload, clean tagged retry,
  and untracking an accidentally committed generated version file.
- A real `uvx gitnextver` release ran in a disposable repository without remotes:
  it committed the fixture change, advanced `v2.3.4` to `v2.3.5`, and left a clean
  tree with the generated version file untracked. Both validation passes passed
  **60 tests, 89.87% coverage** (45.02 s and 44.92 s). The optional Docling model
  integration was deselected as intended for the standard release gate.
- Final wheel `vexy_pdf3md-2.3.5-py3-none-any.whl`, sdist
  `vexy_pdf3md-2.3.5.tar.gz`, and embedded `__version__.py` all reported exactly
  `2.3.5`. `PUBLISH_SKIP_UPLOAD=1` skipped the real upload; mocked tests verified
  the `uv publish` invocation and propagated its failure status.
- The first real release test correctly stopped at a fixture environment leak
  (inherited upload-skip setting); isolated fixture settings fixed it before rerun.
- ShellCheck, Bash syntax, Ruff, ty, `git diff --check`, and primary-checkout
  wheel/source/generated-version equality passed. Build hook output is confirmed
  gitignored and absent from the index.

## 2026-09-10

- Read both projects' source, history, and documentation. vexy-paraltext baseline: 106 tests pass, 91.47% coverage. pdf22md baseline: 90 Swift tests pass.
- Target initially contains LICENSE, .gitignore, and a one-line README; no existing tests or implementation.
- Checked live CLI help for markit, pdf22md, and Tesseract; read official Fire, PyMuPDF, Docling, and Tesseract APIs.
- Added acceptance tests before implementation. Native Codex goal tracks the same task as the OMC ledger; this host is Codex, not Claude Code, so no Claude /goal state is claimed.
- Initial acceptance run failed at collection because `convert` did not yet exist, as intended.
- Implemented 13 small source modules, five adapters, Fire entry points, typed results,
  Git-derived package versions, recursive planning, fallback, and shared media export.
- First complete suite: 39 passed, 88.29% combined statement/branch coverage including
  subprocess workers. Optional Docling scan: 1 passed in 18.70 s.
- Expanded failure/publication tests: 47 passed, 89.30% coverage; rendered-page smoke passed.
- Isolated `uvx hatch test`: 48 passed, 1 optional test deselected.

### Cleanup plan and direct review

Scope: newly written package, tests, examples, and docs only. Preserve conversion
contracts. Check duplicated adapter policy, unused helpers, fragile CLI parsing,
scratch/output collisions, media ownership, subprocess cleanup, and packaging.
Use source and acceptance tests as the spec; compare against the original target HEAD.
The user's single-agent instruction takes precedence over reviewer delegation in the
code-review skill. Both standards and spec review are performed directly.

- Removed scaffold placeholder and unused test imports; reused one shared media path
  and one subprocess boundary for every converter. No registry/plugin framework,
  cache, cloud integration, or custom PDF parser added.
- Wait, but: arbitrary Markdown stems could collide with worker scratch names.
  Exported assets now have a separate staging namespace; `input.pdf.md`,
  `response.json.md`, and `worker.log.md` each pass real conversion/media tests.
- Fixed rotated image bounds before clipping; a real rotated PDF verifies visible
  image pixels, not merely file existence.
- Preserved string arguments through Fire's public parsing decorator; tested a
  numeric password and comma-separated page list through the actual CLI.
- Rejected ambiguous overwrite/fallback types before writes; old media is restored
  on injected Markdown publication failure. Unowned folders remain untouched.
- Added cancellation propagation and stale-response rejection; isolated worker
  termination is verified directly. Windows process-tree limitations are documented.
- Standard suite excludes the expensive optional Docling integration; the final
  explicit all-backend run includes it. Full verification and wheel evidence follow.

### Final verification

- `uv run ruff check src tests examples`: passed.
- `uv run ruff format --check src tests examples`: 18 files formatted.
- `uv run ty check src`: passed.
- `uv run --extra docling pytest -m "" --cov --cov-report=term-missing --cov-report=json -q`:
  **54 passed in 50.28 s; 91.91% coverage**, including subprocesses and branches.
  All five actual backends ran; real Vision, Tesseract, and Docling recognized the
  synthetic scan. No optional integration was skipped in this run.
- `uv run examples/smoke.py`: verified recursive Markdown and rendered page media.
- `uv build`: wheel and source distribution built with hatch-vcs.
- Installed `vexy_pdf3md-0.1.1.dev1+g3642c16bd.d20260910-py3-none-any.whl` into a
  fresh temporary venv. Both `vexy-pdf3md` and `pdf3md` converted a new PDF with text
  and page images from a working directory outside the checkout. Imported version
  matched wheel metadata. Wheel contained the worker and both console entry points.
- Source `this_file` headers, Python syntax, CLI help, and `git diff --check`: passed.

Direct final review against target baseline `3642c16bd3a73a125207c35266a612fb51917c00`:
**Standards: clear; Spec: clear.** No unresolved findings. Reviewed new/untracked
source files in full as well as tracked changes. Cleanup was limited to the new
package. Remaining converter/scan heuristics, basic fallback formatting, rendered
media semantics, Windows child-process limits, and overlapping-invocation limits
are documented in ANALYSIS.md and README.md.

## 2026-10-18: documentation plugins

- Use MaterialX search, inherited metadata and a topic index; keep ordered navigation in awesome-nav.
- The documentation wrapper installs the plugins required by this site.
- Strict documentation build and rendered output checks passed.

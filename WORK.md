---
this_file: WORK.md
---
# Work log

## 2026-11-24 — release and planning

- PyPI records the 1.0.6 wheel as published by `vexyart/vexy-pdf3md` from
  `release.yml` in the `pypi` environment. `publish.sh` dispatches that workflow.
  [Wheel provenance](https://pypi.org/integrity/vexy-pdf3md/1.0.6/vexy_pdf3md-1.0.6-py3-none-any.whl/provenance)
- Four isolated tests passed for explicit and computed tags, invalid input and
  dispatch failure. The local conversion smoke test produced Markdown and a page image.
- `./build.sh docs` passed in strict mode with zero warnings. `./test.sh`
  passed Ruff and ty. Pytest reported 72 passed, one failed, one skipped and
  one deselected, with 92.94% coverage. The sole failure was the native
  `pdf22md` scan test.
- The four completed implementation tasks are recorded in `CHANGELOG.md`.
  `PLAN.md` and `TODO.md` track the remaining checks.

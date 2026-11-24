# Development and release

## Set up

1. Clone the repository and enter it.
2. Create the environment with the development tools:

    ```bash
    uv sync
    ```

    The `dev` dependency group adds pytest, pytest-cov, ruff, ty, hatchling and
    hatch-vcs.

## Run the checks

```bash
./test.sh
```

`test.sh` runs, in order:

1. `ruff check` on `src`, `tests` and `examples`;
2. `ruff format --check` on the same folders;
3. `ty check src` (with the `docling` extra, so the Docling adapter type-checks);
4. `pytest --cov` with a coverage gate of 80%;
5. `examples/smoke.py`.

Arguments to `test.sh` are passed to pytest, for example `./test.sh -k languages`.

Other test commands:

```bash
uv run --extra docling pytest -m optional   # real Docling run; may download models
uvx hatch test                              # isolated hatch test environment
```

Tests marked `optional` need Docling and model downloads and are excluded by default
(`addopts = "-ra -m 'not optional'"` in `pyproject.toml`).

## Test layout

| File | Covers |
| --- | --- |
| `tests/test_conversion.py` | Conversion contracts with real PDFs and isolated workers |
| `tests/test_strategies.py` | Real converter integrations and injected converter failures |
| `tests/test_failures.py` | Publication, process boundaries and path conflicts failing without data loss |
| `tests/test_languages.py` | `--lang` mapping and Tesseract model handling |
| `tests/test_release.py` | Release workflow dispatch and error handling |

## Versioning

The version comes from Git tags through hatch-vcs. During a build or install,
hatch-vcs writes `src/vexy_pdf3md/__version__.py`; that file is listed in
`.gitignore` and must not be committed. After you change tags, rebuild or reinstall
to refresh the version of an editable install.

## Build

```bash
./build.sh            # documentation and package
./build.sh docs       # documentation only, into docs/
./build.sh package    # dist/*.whl and dist/*.tar.gz, then twine check
```

## Documentation

The documentation source is `src_docs/md/`, configured by `src_docs/mkdocs.yml`.
`src_docs/build.sh` uses Python 3.13, ProperDocs and fly-january 0.3.0 or later
with `extra.fly.chrome` set to `none`. GitHub Pages serves the generated `docs/`
directory at <https://vexy.dev/vexy-pdf3md/>.

```bash
src_docs/build.sh          # strict build into docs/
src_docs/build.sh serve    # live preview on http://127.0.0.1:8000
```

The `Docs` workflow (`.github/workflows/docs.yml`) rebuilds `docs/` on every push to
`main` that changes `src_docs/` and commits the result.

## Release

The PyPI project owner must configure a GitHub trusted publisher for
`vexyart/vexy-pdf3md`, workflow `release.yml`, environment `pypi`.

1. Run `./test.sh` and push the release commit to the default branch.
2. With the GitHub CLI authenticated for this repository, run `./publish.sh`
   for the next patch version, or pass an explicit tag such as `./publish.sh v1.4.0`.
3. Check the Release workflow in GitHub Actions. The workflow creates the tag if
   needed, builds the wheel and sdist from that tag, and attaches them to the
   GitHub release. Its `pypi` job uploads the same artifacts using GitHub's OIDC identity.

Pushing a `vMAJOR.MINOR.PATCH` tag directly also triggers the Release workflow.

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
| `tests/test_release.py` | `publish.sh` behaviour in a throwaway Git repository |

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
`src_docs/build.sh` builds it with ProperDocs and the MaterialX theme into `docs/`,
which GitHub Pages serves at <https://vexy.dev/vexy-pdf3md/>.

```bash
src_docs/build.sh          # strict build into docs/
src_docs/build.sh serve    # live preview on http://127.0.0.1:8000
```

The `Docs` workflow (`.github/workflows/docs.yml`) rebuilds `docs/` on every push to
`main` that changes `src_docs/` and commits the result.

## Release

Prerequisites:

- a uv publish credential in the environment, for example `UV_PUBLISH_TOKEN`;
- push access to the Git remote.

Steps:

1. Run the checks: `./test.sh`.
2. Run the release script:

    ```bash
    ./publish.sh
    ```

`publish.sh` does the following:

1. Runs `uvx gitnextver`, which stages and commits **all non-ignored changes**,
   creates the next `vX.Y.Z` tag and pushes.
2. Stops with an error if `HEAD` does not carry a `vX.Y.Z` tag. gitnextver only
   creates a tag when there are changes to commit.
3. Runs `./build.sh package`: removes `dist/`, builds the wheel and sdist, and runs
   `twine check`.
4. Uploads `dist/*` with `uv publish`.

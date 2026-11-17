---
this_file: src_docs/md/api.md
tags: [API]
---

# Python API

The package exports one function and four data classes:

```python
from vexy_pdf3md import Attempt, BatchResult, Options, Result, __version__, convert
```

## `convert()`

```python
def convert(
    input: str | Path,
    output: str | Path | None = None,
    strategies: str | list[str] | tuple[str, ...] = "auto",
    media: bool | str = False,
    workers: int = 2,
    timeout: float = 600,
    fallback: bool = True,
    overwrite: bool = False,
    pages: str = "",
    password: str = "",
    lang: str = "eng",
    dpi: int = 150,
    ocr: str = "auto",
    min_text_ratio: float = 0.5,
) -> BatchResult
```

The arguments mean the same as the [command-line options](cli.md). Differences:

- `strategies` may be a comma-separated string (`"markit,pymupdf"`), `"all"`, or a
  list or tuple of names.
- `media` accepts `True` (same as `"images"`), `False` (same as `"none"`),
  `"images"`, `"pages"` or `"none"`.

### Errors

Configuration and path problems raise before any conversion starts:

- `ValueError` for invalid options (for example `workers=0`, `dpi=50`, an unknown
  strategy), an input that is not a `.pdf` file or folder, a folder with no PDFs, or
  an output collision;
- `FileNotFoundError` (an `OSError`) when `input` does not exist.

Failures of individual documents do not raise. They are returned in the
`BatchResult`.

### Example

```python
from vexy_pdf3md import convert

batch = convert("pdfs", "markdown", strategies="auto", media=True, workers=4)
for item in batch.results:
    print(item.input, item.output, item.status, item.strategy)
    for attempt in item.attempts:
        print(attempt.strategy, attempt.status, attempt.error)
assert batch.ok
```

## `BatchResult`

| Member | Type | Meaning |
| --- | --- | --- |
| `results` | `list[Result]` | One entry per output file |
| `ok` | `bool` (property) | `True` when no result has status `"failed"` |
| `to_dict()` | `dict` | The JSON report the CLI prints |

`to_dict()` returns:

```python
{
    "ok": True,
    "succeeded": 1,   # results with status "success"
    "skipped": 0,     # results with status "skipped"
    "failed": 0,      # results with status "failed"
    "results": [...], # each Result as a dict
}
```

## `Result`

| Field | Type | Meaning |
| --- | --- | --- |
| `input` | `str` | Absolute path of the source PDF |
| `output` | `str` | Path of the Markdown file |
| `requested` | `str` | Strategy requested for this job (`"auto"` or a name) |
| `status` | `"success"`, `"failed"`, `"skipped"` | Outcome |
| `strategy` | `str` or `None` | Converter that wrote the file; `None` if none did |
| `attempts` | `list[Attempt]` | Every converter tried, in order |
| `error` | `str` | Error for a failed document; empty otherwise |

## `Attempt`

| Field | Type | Meaning |
| --- | --- | --- |
| `strategy` | `str` | Converter name |
| `status` | `"success"` or `"failed"` | Outcome of this attempt |
| `seconds` | `float` | Duration, rounded to milliseconds |
| `error` | `str` | Failure message; the password is replaced with `[redacted]` |

## `Options`

`Options` is a frozen data class holding the validated settings. `convert()` builds it
for you; constructing it directly is useful to check settings without converting:

```python
from vexy_pdf3md import Options

Options(strategies=("pymupdf",), workers=4)    # valid
Options(strategies=("auto", "markit"))         # ValueError: auto must stand alone
```

Fields and their checks:

| Field | Default | Check |
| --- | --- | --- |
| `strategies` | `("auto",)` | Non-empty, unique names; `auto` alone |
| `media` | `"none"` | `"none"`, `"images"` or `"pages"` |
| `workers` | `2` | Integer, 1 to 64 |
| `timeout` | `600` | Finite and positive |
| `fallback` | `True` | Boolean |
| `overwrite` | `False` | Boolean |
| `pages` | `""` | String |
| `password` | `""` | String; hidden from `repr()` |
| `lang` | `"eng"` | Names at least one language |
| `dpi` | `150` | Integer, 72 to 600 |
| `ocr` | `"auto"` | `"auto"`, `"always"` or `"never"` |
| `min_text_ratio` | `0.5` | 0 to 1 |

## `__version__`

The installed version string, generated from the Git tag at build time by hatch-vcs.

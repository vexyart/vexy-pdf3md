# Installation

## Prerequisites

- Python 3.12 or later.
- [uv](https://docs.astral.sh/uv/) for the commands shown on this page.

## Install the package

Install from PyPI:

```bash
uv tool install vexy-pdf3md
vexy-pdf3md --help
```

To install with the Docling converter included:

```bash
uv tool install 'vexy-pdf3md[docling]'
```

The `all` extra currently installs the same set as `docling`.

### Install from a checkout

1. Clone the repository and enter it:

    ```bash
    git clone https://github.com/vexyart/vexy-pdf3md.git
    cd vexy-pdf3md
    ```

2. Create the environment:

    ```bash
    uv sync
    ```

3. Run the CLI from the checkout:

    ```bash
    uv run vexy-pdf3md --help
    ```

4. Optional: install the checkout as a CLI that works outside the repository:

    ```bash
    uv tool install .
    # or, with Docling:
    uv tool install '.[docling]'
    ```

## Commands installed

The package installs the same command under two names:

- `vexy-pdf3md`
- `pdf3md`

`python -m vexy_pdf3md` runs the same CLI.

## Optional converters

PyMuPDF is installed with the package and works immediately for PDFs with a text
layer. The other converters are optional. The package looks for them on `PATH`, or,
for Docling, checks whether the `docling` Python package can be imported.

### markit

Install from the [upstream instructions](https://github.com/shift-labs-ai/markit).
`vexy-pdf3md` runs it as `markit -q --no-images FILE.pdf`. markit is the first choice
for text-layer PDFs and handles multi-column layouts.

### pdf22md (macOS)

Build and install [pdf22md](https://github.com/twardoch/pdf22md). It provides PDFKit
text extraction and Apple Vision OCR. It is the first choice for scanned PDFs when it
is installed.

### Tesseract

On macOS:

```bash
brew install tesseract
```

On other systems, install your distribution's Tesseract package.

Language models named by `--lang` that are not in the system `tessdata` folder are
downloaded from `tessdata_fast` into `~/.cache/vexy-pdf3md/tessdata` on first use.
If `XDG_CACHE_HOME` is set, the cache is `$XDG_CACHE_HOME/vexy-pdf3md/tessdata`
instead. To work offline, install the language packs with your package manager, for
example:

```bash
brew install tesseract-lang
```

### Docling

From a checkout:

```bash
uv sync --extra docling
uv run --extra docling vexy-pdf3md book.pdf --strategies=docling
```

The extra requires `docling>=2.126,<3` and `pydantic>=2.12`. The Docling adapter uses
Tesseract for OCR when `tesseract` is on `PATH`. Docling may download layout and table
models on first use.

## Check what is available

`vexy-pdf3md` has no separate "list converters" command. To see which external tools
are on your `PATH`:

```bash
which markit pdf22md tesseract
tesseract --list-langs
```

Automatic selection only uses converters that are installed. If you name a missing
converter with `--strategies`, that attempt fails and the next eligible converter is
tried (unless `--fallback=False`).

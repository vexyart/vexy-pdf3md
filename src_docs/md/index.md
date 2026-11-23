# vexy-pdf3md {data-toc-label="pdf3md"}

`vexy-pdf3md` converts one PDF, or every PDF in a folder tree, to Markdown. It runs
locally and calls no cloud OCR or AI service.

You can name a converter, let the package choose one, or run several converters side
by side and compare the results. When a converter fails, the package tries another
eligible one. Each result records every attempt and the converter that produced the
file.

## What goes in, what comes out

You give the tool a PDF file or a folder:

```bash
vexy-pdf3md book.pdf
```

The tool writes `book.md` beside the PDF and prints a JSON report to stdout:

```json
{
  "ok": true,
  "succeeded": 1,
  "skipped": 0,
  "failed": 0,
  "results": [
    {
      "input": "/path/to/book.pdf",
      "output": "/path/to/book.md",
      "requested": "auto",
      "status": "success",
      "strategy": "pymupdf",
      "attempts": [{"strategy": "pymupdf", "status": "success", "seconds": 0.308, "error": ""}],
      "error": ""
    }
  ]
}
```

`requested` is the strategy you asked for. `strategy` is the converter that actually
wrote the file. `attempts` lists every converter that was tried, in order.

## Converters

`vexy-pdf3md` does not convert PDFs itself. It calls one of five converters, called
*strategies*:

| Strategy | Kind | How it is found |
| --- | --- | --- |
| `markit` | Text layer, column-aware | `markit` executable on `PATH` |
| `pymupdf` | Text layer, basic blocks and headings | Always available (core dependency) |
| `pdf22md` | macOS PDFKit text and Apple Vision OCR | `pdf22md` executable on `PATH` |
| `tesseract` | OCR of rendered pages | `tesseract` executable on `PATH` |
| `docling` | Layout and table reconstruction, OCR | `docling` extra installed |

PyMuPDF is a core dependency, so a fresh install can already convert PDFs that have a
text layer.

## Where to go next

- [Installation](installation.md): install the package and the optional converters.
- [Quick start](quickstart.md): convert a file, a folder, and a scan.
- [Command line](cli.md): every option, its default and its range.
- [Strategies and fallback](strategies.md): how the converter is chosen and when a
  result is rejected.
- [Output layout and media](output.md): file names, suffixes, media folders and
  overwrite rules.
- [Python API](api.md): `convert()` and the result objects.
- [Architecture](architecture.md): the worker processes, timeouts and staged writes.
- [Troubleshooting](troubleshooting.md): common failures and what to do.
- [Development and release](contributing.md): tests, builds and publishing.

## License

The package's own code is licensed under Apache-2.0. Dependencies keep their own
licenses. PyMuPDF is under AGPL or a commercial license.

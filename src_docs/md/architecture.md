# Architecture

`vexy-pdf3md` is about 1,000 lines of Python in `src/vexy_pdf3md/`. This page
follows one PDF through the code.

## Modules

| Module | Role |
| --- | --- |
| `cli.py` | Fire CLI: logging setup, JSON report, exit status |
| `converter.py` | `convert()`: builds options, plans jobs, runs them, collects attempts |
| `models.py` | `Options`, `Attempt`, `Result`, `BatchResult`; strategy names |
| `paths.py` | Plans input → output pairs and rejects collisions |
| `process.py` | Starts worker processes, enforces timeouts, kills process groups |
| `worker.py` | Worker entry point: inspect, convert or export media |
| `inspection.py` | Page selection, scan detection, temporary page-limited PDF |
| `selection.py` | Candidate ranking and output quality checks |
| `backends.py` | Adapters for markit, PyMuPDF, pdf22md, Tesseract and Docling |
| `languages.py` | Maps `--lang` codes and fetches Tesseract models |
| `media.py` | Renders images or pages and builds the `## Media` section |
| `publication.py` | Moves finished files into place |

## One PDF, step by step

Take `vexy-pdf3md book.pdf --media`.

1. **Validate.** `convert()` turns the arguments into an `Options` object. Invalid
   values raise `ValueError`; the CLI prints the error and exits with status `2`.
2. **Plan.** `paths.plan()` resolves `book.pdf`, chooses `book.md`, and checks for
   collisions. The result is a list of `Job(source, output, requested)` entries.
3. **Schedule.** A thread pool of `--workers` threads runs the jobs. The threads do
   no PDF work; each one waits on worker processes.
4. **Inspect.** A worker process runs `inspection.inspect()` and returns a profile:
   selected pages, character counts per page, pages that look scanned, and whether
   the document needs OCR.
5. **Rank.** `selection.candidates()` turns the profile and options into an ordered
   list of converters.
6. **Attempt.** For each candidate, a new worker process writes `result.md` into a
   temporary folder (named `.pdf3md-*`) next to `book.md`. The parent reads it and
   runs `check_quality()`. On failure the error is recorded and the next candidate is
   tried.
7. **Media.** After a successful attempt, another worker renders the images into the
   temporary folder and returns the `## Media` Markdown, which is appended.
8. **Publish.** `publication.publish()` moves the media folder into place first, then
   the Markdown file. The Markdown is the commit point: without `--overwrite` it is
   created with a hard link, so an existing file is never replaced.

## Why worker processes

PyMuPDF must not be used from several threads at once, and native converters
(Docling in particular) can crash the process on some scans. A Python exception
handler cannot catch a segmentation fault. So all PDF work — inspection, conversion
and media rendering — runs in a child process started as
`python -m vexy_pdf3md.worker RESPONSE.json`.

The request, including any password, is sent on the worker's stdin as JSON. The
worker writes its answer to the response file, not stdout, so library output cannot
corrupt it. Worker stdout and stderr go to `worker.log`; the last part of that log is
included in the error if the worker exits without a response.

## Timeouts and cancellation

Each worker gets `--timeout` seconds. On POSIX systems the worker starts in its own
session; on timeout or Ctrl-C the whole process group is killed with `SIGKILL`,
including converter subprocesses such as `markit` or `tesseract`. On Windows only the
direct worker process is killed.

If the batch is interrupted, a shared cancel flag is set. Workers that are running
are killed within about 0.2 seconds, and jobs that have not started a worker yet do
not start one.

## Staged writes

All files are written to a temporary folder beside the destination first. If a
conversion fails, nothing at the destination changes. If moving the new media folder
into place fails, the previous media folder is restored from a backup.

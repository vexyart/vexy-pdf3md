---
this_file: PLAN.md
---
# Implementation plan

Status: all five steps completed and verified on 2026-09-10. Evidence: WORK.md.

Scope: convert one PDF or a recursive tree to Markdown, selecting and falling back between isolated local converters, with consistent variant and media paths.

1. Inspect both source implementations, baseline tests, and official APIs. Record decisions in ANALYSIS.md.
2. Define output, failure, media, and CLI contracts in tests before implementation.
3. Implement typed options/results, deterministic path planning, isolated PDF inspection and converter workers, selection and quality checks, bounded concurrency, safe publication, and Fire CLI.
4. Test real native extraction, markit, macOS Vision, Tesseract OCR, fallback, corrupt PDFs, passwords, page ranges, media, collisions, timeouts, and installed wheel.
5. Run cleanup, direct standards/spec review, lint, types, coverage, and build; record evidence.

Design: use existing converters for parsing/OCR. Python orchestration chooses tools and owns paths. Worker subprocesses isolate native libraries and enforce time limits. No cloud services or credentials needed. Optional Docling may download its own models on first use.

Acceptance: one output per requested strategy, suffixes only for multiple strategies, relative media links, no overwrite by default, and a nonzero CLI status when any job fails. Fall back on unavailable tools, crashes, timeout, empty text, replacement-character corruption, or substantial loss against the PDF text layer. Scanned and mixed documents require OCR unless explicitly disabled.

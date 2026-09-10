#!/usr/bin/env bash
# this_file: test.sh
set -euo pipefail
cd "$(dirname "$0")"
uv run ruff check src tests examples
uv run ruff format --check src tests examples
uv run --extra docling ty check src
uv run pytest --cov --cov-report=term-missing "$@"
uv run examples/smoke.py

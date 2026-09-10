# this_file: src/vexy_pdf3md/__init__.py
"""Local PDF-to-Markdown conversion with isolated, interchangeable strategies."""

from .__version__ import __version__
from .converter import convert
from .models import Attempt, BatchResult, Options, Result

__all__ = ["Attempt", "BatchResult", "Options", "Result", "__version__", "convert"]

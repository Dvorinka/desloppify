"""Shared assembly helpers for Python language configuration."""

from __future__ import annotations

import ast
import os
from functools import partial
from pathlib import Path

from desloppify.base.discovery.source import find_py_files
from desloppify.base.discovery.paths import get_area
from desloppify.engine.detectors.base import FunctionInfo
from desloppify.languages.python.extractors import extract_py_functions

_get_py_area = partial(get_area, min_depth=3)


def py_extract_functions(path: Path) -> list[FunctionInfo]:
    """Extract all Python functions for duplicate detection."""
    functions = []
    for filepath in find_py_files(path):
        functions.extend(extract_py_functions(filepath))
    return functions


def py_has_main_guard(filepath: str) -> bool:
    """Whether the file carries an ``if __name__ == "__main__":`` entry guard."""
    try:
        tree = ast.parse(Path(filepath).read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return False
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Eq)
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value == "__main__"
        ):
            return True
    return False


def scan_root_from_files(files: list[str]) -> Path | None:
    """Derive the common ancestor directory from a list of file paths."""
    py_files = [f for f in files if f.endswith(".py")]
    if not py_files:
        return None
    try:
        common = Path(os.path.commonpath(py_files))
        return common if common.is_dir() else common.parent
    except ValueError:
        return None


__all__ = [
    "_get_py_area",
    "py_extract_functions",
    "py_has_main_guard",
    "scan_root_from_files",
]

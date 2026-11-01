"""Dynamic import discovery for Python dependency hints."""

from __future__ import annotations

import ast
import logging
from pathlib import Path

from desloppify.base.discovery.paths import get_project_root
from desloppify.base.discovery.source import find_py_files

from .deps_resolution import resolve_absolute_import

logger = logging.getLogger(__name__)


def find_python_dynamic_imports(path: Path, extensions: list[str]) -> set[str]:
    """Find module specifiers referenced by ``importlib.import_module`` calls."""
    del extensions
    targets: set[str] = set()
    for py_file in find_py_files(path):
        py_path = Path(py_file)
        if not py_path.is_absolute():
            py_path = get_project_root() / py_path
        try:
            tree = ast.parse(py_path.read_text(), filename=str(py_path))
        except (SyntaxError, UnicodeDecodeError, OSError) as exc:
            logger.debug(
                "Skipping unreadable file %s in dynamic import scan: %s",
                py_file,
                exc,
            )
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (
                isinstance(func, ast.Attribute)
                and func.attr == "import_module"
                and isinstance(func.value, ast.Name)
                and func.value.id == "importlib"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                continue

            spec = node.args[0].value
            resolved = resolve_absolute_import(spec, path)
            if resolved:
                targets.add(resolved)
            else:
                targets.add(spec)
    return targets


__all__ = ["find_python_dynamic_imports"]

"""TypeScript move helpers for import replacement computation."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from desloppify.base.output.fallbacks import log_best_effort_failure
from desloppify.base.discovery.paths import get_src_path

VERIFY_HINT = "npx tsc --noEmit"
logger = logging.getLogger(__name__)


def _dedup(replacements: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Deduplicate replacement tuples while preserving order."""
    seen: set[tuple[str, str]] = set()
    result = []
    for pair in replacements:
        if pair not in seen:
            seen.add(pair)
            result.append(pair)
    return result


def _strip_ts_ext(path: str) -> str:
    """Strip .ts/.tsx/.js/.jsx extension from an import path."""
    for ext in (".tsx", ".ts", ".jsx", ".js"):
        if path.endswith(ext):
            return path[: -len(ext)]
    return path


def _compute_ts_specifiers(from_file: str, to_file: str) -> tuple[str | None, str]:
    """Compute both @/ alias and relative import specifiers for a TS file."""
    to_path = Path(to_file)
    src_path = get_src_path()

    alias = None
    if to_path == src_path or src_path in to_path.parents:
        to_rel_src = to_path.relative_to(src_path)
        alias = "@/" + _strip_ts_ext(str(to_rel_src).replace("\\", "/"))
        if alias.endswith("/index"):
            alias = alias[:-6]
    else:
        logger.debug(
            "Unable to compute TS alias for %s relative to src %s", to_file, src_path
        )

    from_dir = Path(from_file).parent
    relative = os.path.relpath(to_file, from_dir).replace("\\", "/")
    relative = _strip_ts_ext(relative)
    if not relative.startswith("."):
        relative = "./" + relative
    if relative.endswith("/index"):
        relative = relative[:-6]

    return alias, relative


_EXPLICIT_EXTS = (".ts", ".tsx", ".js", ".jsx")


def _spec_forms(spec: str, is_index: bool) -> dict[str, str]:
    """Map written-form suffixes to full specifiers for one computed spec.

    A non-index module accepts explicit extensions on the bare specifier;
    an index module accepts them only on the `/index` spelling — `./x.ts`
    names the file `x.ts`, never `x/index.ts`."""
    forms = {}
    for ext in ("", *_EXPLICIT_EXTS):
        if is_index:
            forms["/index" + ext] = spec + "/index" + ext
        else:
            forms[ext] = spec + ext
    forms[""] = spec
    return forms


def _form_replacements(
    content: str,
    old_spec: str | None,
    new_spec: str | None,
    *,
    old_is_index: bool,
    new_is_index: bool,
) -> list[tuple[str, str]]:
    """Find specifier spellings present in content and pair them with the
    equivalent spelling of the destination, preserving explicit extensions
    and index-module forms."""
    if old_spec is None or new_spec is None or old_spec == new_spec:
        return []
    old_forms = _spec_forms(old_spec, old_is_index)
    new_forms = _spec_forms(new_spec, new_is_index)
    replacements = []
    for suffix, old_form in old_forms.items():
        new_form = new_forms.get(suffix)
        if new_form is None:
            # The written form has no equivalent on the destination shape:
            # fold `/index` spellings onto the bare specifier or vice versa.
            alt = (
                suffix[len("/index") :]
                if suffix.startswith("/index")
                else "/index" + suffix
            )
            new_form = new_forms[alt]
        for quote in ("'", '"'):
            target = f"{quote}{old_form}{quote}"
            if target in content:
                replacements.append((target, f"{quote}{new_form}{quote}"))
    return replacements


def find_replacements(
    source_abs: str,
    dest_abs: str,
    graph: dict,
) -> dict[str, list[tuple[str, str]]]:
    """Compute all import string replacements needed for a TS file move."""
    changes: dict[str, list[tuple[str, str]]] = {}
    entry = graph.get(source_abs)
    if not entry:
        return changes

    importers = entry.get("importers", set())

    for importer in importers:
        if importer == source_abs:
            continue

        old_alias, old_relative = _compute_ts_specifiers(importer, source_abs)
        new_alias, new_relative = _compute_ts_specifiers(importer, dest_abs)

        replacements = []
        try:
            content = Path(importer).read_text()
        except (OSError, UnicodeDecodeError) as exc:
            log_best_effort_failure(
                logger, f"read importer for TypeScript move {importer}", exc
            )
            continue

        old_is_index = Path(source_abs).stem == "index"
        new_is_index = Path(dest_abs).stem == "index"
        for old_spec, new_spec in [
            (old_alias, new_alias),
            (old_relative, new_relative),
        ]:
            replacements.extend(
                _form_replacements(
                    content,
                    old_spec,
                    new_spec,
                    old_is_index=old_is_index,
                    new_is_index=new_is_index,
                )
            )

        if replacements:
            changes[importer] = _dedup(replacements)

    return changes


def find_self_replacements(
    source_abs: str,
    dest_abs: str,
    graph: dict,
) -> list[tuple[str, str]]:
    """Compute replacements for the moved file's own relative imports."""
    replacements = []
    entry = graph.get(source_abs)
    if not entry:
        return replacements

    try:
        content = Path(source_abs).read_text()
    except (OSError, UnicodeDecodeError) as exc:
        log_best_effort_failure(
            logger, f"read moved TypeScript source {source_abs}", exc
        )
        return replacements

    for imported_file in entry.get("imports", set()):
        _, old_relative = _compute_ts_specifiers(source_abs, imported_file)
        _, new_relative = _compute_ts_specifiers(dest_abs, imported_file)
        replacements.extend(
            _form_replacements(
                content,
                old_relative,
                new_relative,
                old_is_index=Path(imported_file).stem == "index",
                new_is_index=Path(imported_file).stem == "index",
            )
        )

    return _dedup(replacements)


def filter_intra_package_importer_changes(
    source_file: str,
    replacements: list[tuple[str, str]],
    moving_files: set[str],
) -> list[tuple[str, str]]:
    """TypeScript intra-package importer changes are valid as-is."""
    del source_file, moving_files
    return replacements


def filter_directory_self_changes(
    source_file: str,
    self_changes: list[tuple[str, str]],
    moving_files: set[str],
) -> list[tuple[str, str]]:
    """TypeScript self-import changes remain valid when moving directories."""
    del source_file, moving_files
    return self_changes

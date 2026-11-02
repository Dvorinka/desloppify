"""Orphaned file detection: files with zero importers that aren't entry points."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from desloppify.base.discovery.file_paths import count_lines, rel, resolve_path

_DUNDER_ALL_RE = re.compile(r"^__all__\s*[:=]", re.MULTILINE)

# ---------------------------------------------------------------------------
# Next.js App Router convention files
# ---------------------------------------------------------------------------

# Files that are entry points when inside an app/ directory
_NEXTJS_APP_DIR_CONVENTIONS: set[str] = {
    "page",
    "layout",
    "loading",
    "error",
    "not-found",
    "global-error",
    "route",
    "template",
    "default",
    "opengraph-image",
    "twitter-image",
    "sitemap",
    "robots",
    "icon",
    "apple-icon",
}

# Files that are entry points at the project root (or src/)
_NEXTJS_ROOT_CONVENTIONS: set[str] = {
    "middleware",
    "proxy",
    "instrumentation",
    "instrumentation-client",
}

_NEXTJS_EXTENSIONS: set[str] = {".ts", ".tsx", ".js", ".jsx"}


# ---------------------------------------------------------------------------
# React Router / Remix convention files
# ---------------------------------------------------------------------------

# Everything under app/routes/ is a route module, loaded by the framework's
# file-based router and imported by nothing.
_REACT_ROUTER_ROUTE_DIRS: tuple[str, ...] = ("routes",)

# Framework entry points that sit beside the routes directory.
_REACT_ROUTER_CONVENTIONS: set[str] = {
    "root",
    "entry.client",
    "entry.server",
}

_REACT_ROUTER_CONFIGS: tuple[str, ...] = (
    "react-router.config.js",
    "react-router.config.mjs",
    "react-router.config.ts",
    "remix.config.js",
    "remix.config.mjs",
    "remix.config.ts",
)


def _detect_react_router_project(path: Path) -> bool:
    """Return True if this directory declares a React Router or Remix project.

    A config file is the cheap signal. Failing that, the dependency is checked,
    because the framework's own template ships a Vite config rather than a
    react-router.config file.
    """
    for name in _REACT_ROUTER_CONFIGS:
        if (path / name).is_file():
            return True

    package_json = path / "package.json"
    if package_json.is_file():
        try:
            text = package_json.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return False
        return '"@react-router/' in text or '"@remix-run/' in text
    return False


def _react_router_project_root(
    directory: Path, cache: dict[Path, Path | None]
) -> Path | None:
    """Find the nearest React Router project root, package-bounded."""
    visited = []
    current = directory
    while current not in cache:
        visited.append(current)
        if _detect_react_router_project(current):
            root = current
            break
        if (current / "package.json").is_file() or current.parent == current:
            root = None
            break
        current = current.parent
    else:
        root = cache[current]
    for parent in visited:
        cache[parent] = root
    return root


def _is_react_router_convention_entry(rel_path: str) -> bool:
    """Return True if *rel_path* is a React Router / Remix convention file.

    Route modules and the framework entry points have no importers by design —
    the router loads them from the filesystem — so reporting them as orphaned
    is a false positive on every project of this shape.
    """
    p = Path(rel_path)
    if p.suffix not in _NEXTJS_EXTENSIONS:
        return False

    parts = p.parts

    # Any file beneath an app/routes/ (or src/routes/) directory.
    for routes_dir in _REACT_ROUTER_ROUTE_DIRS:
        if routes_dir in parts[:-1]:
            return True

    # root.jsx, entry.client.jsx, entry.server.jsx beside the routes directory.
    # `.stem` only strips the last suffix, so entry.client.jsx stems to
    # "entry.client", which is exactly what is being matched.
    if p.stem in _REACT_ROUTER_CONVENTIONS and len(parts) <= 3:
        return True

    return False


def _detect_nextjs_project(path: Path) -> bool:
    """Return True if this directory declares a Next.js project."""
    for name in ("next.config.js", "next.config.mjs", "next.config.ts"):
        if (path / name).is_file():
            return True
    return False


def _nextjs_project_root(directory: Path, cache: dict[Path, Path | None]) -> Path | None:
    """Find the nearest Next config without crossing another package boundary."""
    visited = []
    current = directory
    while current not in cache:
        visited.append(current)
        if _detect_nextjs_project(current):
            root = current
            break
        if (current / "package.json").is_file() or current.parent == current:
            root = None
            break
        current = current.parent
    else:
        root = cache[current]
    for parent in visited:
        cache[parent] = root
    return root


def _is_nextjs_convention_entry(rel_path: str) -> bool:
    """Return True if *rel_path* is a Next.js App Router convention file.

    Checks:
    - Files with convention names inside ``app/`` or ``src/app/``
    - Root-level convention files (middleware, proxy, instrumentation)
    """
    p = Path(rel_path)
    ext = p.suffix
    if ext not in _NEXTJS_EXTENSIONS:
        return False

    stem = p.stem
    parts = p.parts

    # Root-level conventions: middleware.ts, instrumentation.ts, etc.
    # These can live at the project root or inside src/
    if stem in _NEXTJS_ROOT_CONVENTIONS and (
        len(parts) == 1 or (len(parts) == 2 and parts[0] == "src")
    ):
        return True

    app_depth = 1 if parts[:1] == ("app",) else 2 if parts[:2] == ("src", "app") else 0
    # Next excludes private folders from routing, including their convention files.
    return bool(
        stem in _NEXTJS_APP_DIR_CONVENTIONS
        and app_depth
        and not any(part.startswith("_") for part in parts[app_depth:-1])
    )


# ---------------------------------------------------------------------------
# Python framework conventions (Django, Alembic)
# ---------------------------------------------------------------------------

# Module names Django autodiscovers or loads by dotted-string reference.
_DJANGO_CONVENTION_STEMS: set[str] = {
    "admin",
    "apps",
    "middleware",
    "models",
    "tasks",
    "routers",
    "context_processors",
    "signals",
    "receivers",
    "views",
    "forms",
    "serializers",
    "permissions",
    "settings",
    "wsgi",
    "asgi",
    "manage",
    "conftest",
}


def _django_project_root(directory: Path, cache: dict[Path, Path | None]) -> Path | None:
    """Find the nearest ancestor holding manage.py without crossing a package root."""
    visited = []
    current = directory
    while current not in cache:
        visited.append(current)
        if (current / "manage.py").is_file():
            root = current
            break
        if (current / "pyproject.toml").is_file() or current.parent == current:
            root = None
            break
        current = current.parent
    else:
        root = cache[current]
    for parent in visited:
        cache[parent] = root
    return root


def _is_django_convention_entry(rel_path: str) -> bool:
    """Whether *rel_path* under a Django root is a framework-loaded module."""
    p = Path(rel_path)
    if p.suffix != ".py":
        return False
    stem = p.stem
    if "templatetags" in p.parts or "migrations" in p.parts or "management" in p.parts:
        return True
    if stem == "urls" or stem.startswith("urls_") or stem.endswith("_urls"):
        return True
    return stem in _DJANGO_CONVENTION_STEMS


def _alembic_script_location(root: Path) -> Path | None:
    """Read script_location from alembic.ini at *root*, if present."""
    ini = root / "alembic.ini"
    if not ini.is_file():
        return None
    try:
        text = ini.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = re.search(r"(?m)^\s*script_location\s*=\s*(\S+)", text)
    if not match:
        return root / "alembic"
    return (root / match.group(1).replace("%(here)s", ".")).resolve()


def _alembic_project_root(directory: Path, cache: dict[Path, Path | None]) -> Path | None:
    visited = []
    current = directory
    while current not in cache:
        visited.append(current)
        if (current / "alembic.ini").is_file():
            root = current
            break
        if (current / "pyproject.toml").is_file() or current.parent == current:
            root = None
            break
        current = current.parent
    else:
        root = cache[current]
    for parent in visited:
        cache[parent] = root
    return root


def _is_alembic_runtime_file(source: Path, project_root: Path) -> bool:
    """Whether *source* is loaded by Alembic rather than ordinary imports."""
    location = _alembic_script_location(project_root)
    if location is None:
        return False
    try:
        relative = source.relative_to(location)
    except ValueError:
        return False
    if relative.name == "env.py" and len(relative.parts) == 1:
        return True
    return len(relative.parts) == 2 and relative.parts[0] == "versions" and source.suffix == ".py"


@dataclass
class OrphanedDetectionOptions:
    """Optional behavior flags for orphaned-file detection."""

    extra_entry_patterns: list[str] | None = None
    extra_barrel_names: set[str] | None = None
    dynamic_import_finder: Callable[[Path, list[str]], set[str]] | None = None
    alias_resolver: Callable[[str], str] | None = None
    entry_point_detector: Callable[[str], bool] | None = None
    detect_frameworks: bool = True


def _has_dunder_all(filepath: str) -> bool:
    """Return True if the file defines ``__all__``, signaling a public API surface."""
    try:
        text = Path(filepath).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return _DUNDER_ALL_RE.search(text) is not None


def _is_dynamically_imported(
    filepath: str,
    dynamic_targets: set[str],
    alias_resolver: Callable[[str], str] | None = None,
) -> bool:
    """Check if a file is referenced by any dynamic/side-effect import."""
    r = rel(filepath)
    stem = Path(filepath).stem
    name_no_ext = str(Path(r).with_suffix(""))

    for target in dynamic_targets:
        resolved = alias_resolver(target) if alias_resolver else target
        resolved = resolved.lstrip("./")
        if resolved == name_no_ext or resolved == r:
            return True
        if name_no_ext.endswith("/" + resolved) or name_no_ext.endswith(resolved):
            return True
        if resolved.endswith("/" + stem) or resolved == stem:
            return True
        if resolved.endswith("/" + Path(filepath).name):
            return True

    return False


def detect_orphaned_files(
    path: Path,
    graph: dict,
    extensions: list[str],
    options: OrphanedDetectionOptions | None = None,
) -> tuple[list[dict], int]:
    """Find files with zero importers that aren't known entry points."""
    resolved_options = options or OrphanedDetectionOptions()
    all_entry_patterns = resolved_options.extra_entry_patterns or []
    all_barrel_names = resolved_options.extra_barrel_names or set()
    dynamic_import_finder = resolved_options.dynamic_import_finder
    alias_resolver = resolved_options.alias_resolver

    # Resolve framework ownership per file for monorepos and subtree scans.
    nextjs_roots: dict[Path, Path | None] = {}
    react_router_roots: dict[Path, Path | None] = {}
    django_roots: dict[Path, Path | None] = {}
    alembic_roots: dict[Path, Path | None] = {}

    dynamic_targets = (
        dynamic_import_finder(path, extensions) if dynamic_import_finder else set()
    )

    total_files = len(graph)
    entries = []
    for filepath, entry in graph.items():
        if entry["importer_count"] > 0 or entry.get("is_entry_point") is True:
            continue

        r = rel(filepath)

        if any(p in r for p in all_entry_patterns):
            continue

        basename = Path(filepath).name
        if basename in all_barrel_names:
            continue

        if resolved_options.entry_point_detector and resolved_options.entry_point_detector(
            filepath
        ):
            continue

        if resolved_options.detect_frameworks:
            source = Path(resolve_path(filepath))
            project_root = _nextjs_project_root(source.parent, nextjs_roots)
            if project_root and _is_nextjs_convention_entry(str(source.relative_to(project_root))):
                continue
            if source.suffix in _NEXTJS_EXTENSIONS:
                react_router_root = _react_router_project_root(
                    source.parent, react_router_roots
                )
                if react_router_root and _is_react_router_convention_entry(
                    str(source.relative_to(react_router_root))
                ):
                    continue
            if source.suffix == ".py":
                django_root = _django_project_root(source.parent, django_roots)
                if django_root and _is_django_convention_entry(
                    str(source.relative_to(django_root))
                ):
                    continue
                alembic_root = _alembic_project_root(source.parent, alembic_roots)
                if alembic_root and _is_alembic_runtime_file(source.resolve(), alembic_root):
                    continue

        if dynamic_targets and _is_dynamically_imported(
            filepath, dynamic_targets, alias_resolver
        ):
            continue

        if _has_dunder_all(filepath):
            continue

        try:
            loc = count_lines(Path(filepath))
        except (OSError, UnicodeDecodeError):
            loc = 0

        if loc < 10:
            continue

        entries.append(
            {
                "file": filepath,
                "loc": loc,
                "import_count": entry.get("import_count", 0),
            }
        )

    return sorted(entries, key=lambda e: -e["loc"]), total_files

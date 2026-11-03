"""Config instantiation and public language resolution helpers."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

from desloppify.base.discovery.source import (
    DEFAULT_EXCLUSIONS,
    get_exclusions,
)

from . import state
from ..base.types import LangConfig
from ..contract_validation import validate_lang_contract
from .discovery import load_all, reset_runtime_state

_MARKER_GLOB_CHARS = ("*", "?", "[")


def _reset_dynamic_registries_for_refresh() -> None:
    """Reset mutable registries before refresh-driven discovery."""
    from desloppify.base.registry import reset_registered_detectors
    from desloppify.engine._scoring.policy.core import reset_registered_scoring_policies

    reset_registered_detectors()
    reset_registered_scoring_policies()
    reset_runtime_state()


def make_lang_config(name: str, cfg_cls: type) -> LangConfig:
    """Instantiate and validate a language config."""
    try:
        cfg = cfg_cls()
    except (TypeError, ValueError, AttributeError, RuntimeError, OSError) as ex:
        raise ValueError(
            f"Failed to instantiate language config '{name}': {ex}"
        ) from ex
    validate_lang_contract(name, cfg)
    return cfg


def get_lang(
    name: str,
    *,
    refresh_registry: bool = False,
) -> LangConfig:
    """Get a language config by name.

    All plugins (full and generic) store LangConfig instances in the registry.
    Test doubles that store plain classes are instantiated on demand as a fallback.
    """
    if refresh_registry:
        _reset_dynamic_registries_for_refresh()
        load_all(force_reload=True)
    elif not state.is_registered(name):
        load_all()
    if not state.is_registered(name):
        available = ", ".join(sorted(state.all_keys()))
        raise ValueError(f"Unknown language: {name!r}. Available: {available}")
    obj = state.get(name)
    if isinstance(obj, LangConfig):
        return obj
    return make_lang_config(name, obj)  # fallback for test doubles


def auto_detect_lang(
    project_root: Path,
    *,
    refresh_registry: bool = False,
) -> str | None:
    """Auto-detect language from project files.

    When multiple config files are present (e.g. package.json + pyproject.toml),
    counts actual source files to pick the dominant language instead of relying
    on first-match ordering.
    """
    if refresh_registry:
        _reset_dynamic_registries_for_refresh()
    load_all(force_reload=refresh_registry)
    candidates: list[str] = []
    configs: dict[str, LangConfig] = {}

    for lang_name, obj in state.all_items():
        cfg = obj if isinstance(obj, LangConfig) else make_lang_config(lang_name, obj)
        configs[lang_name] = cfg
        markers = getattr(cfg, "detect_markers", []) or []
        if markers and any(_detect_marker_exists(project_root, marker) for marker in markers):
            candidates.append(lang_name)

    if not candidates:
        # Marker-less fallback: pick language with most source files.
        best, best_count = None, 0
        for lang_name, cfg in configs.items():
            count = _scannable_file_count(cfg, project_root)
            if count > best_count:
                best, best_count = lang_name, count
        return best if best_count > 0 else None

    if len(candidates) == 1:
        return candidates[0]

    # Multiple candidates: choose language with most source files.
    best, best_count = None, -1
    for lang_name in candidates:
        count = _scannable_file_count(configs[lang_name], project_root)
        if count > best_count:
            best, best_count = lang_name, count
    return best


def _scannable_file_count(cfg: LangConfig, project_root: Path) -> int:
    """Count source files honoring configured exclusions.

    The marker-less fallback used to count raw ``file_finder`` results, so a
    language whose vendored/build-output headers sit inside excluded
    directories could win detection over the project's real language
    (upstream #727). Count only files that scan would actually see.
    """
    if not cfg.file_finder:
        return 0
    excluded_dirs = {
        Path(entry).resolve()
        for entry in _excluded_dir_paths(project_root)
    }
    glob_patterns = _excluded_globs()
    count = 0
    for filepath in cfg.file_finder(project_root):
        path = Path(filepath)
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path.absolute()
        if any(
            resolved == excluded or excluded in resolved.parents
            for excluded in excluded_dirs
        ):
            continue
        try:
            rel = str(resolved.relative_to(project_root.resolve()))
        except ValueError:
            rel = str(path)
        if any(fnmatch(rel, pattern) for pattern in glob_patterns):
            continue
        count += 1
    return count


def _excluded_dir_paths(project_root: Path) -> list[str]:
    """Absolute paths of non-glob exclusion dirs under *project_root*."""
    root = Path(project_root).resolve()
    out: list[str] = []
    for pattern in (*DEFAULT_EXCLUSIONS, *get_exclusions()):
        if not pattern or "*" in pattern or "?" in pattern or "[" in pattern:
            continue
        candidate = Path(pattern)
        out.append(str(candidate if candidate.is_absolute() else root / candidate))
    return out


def _excluded_globs() -> tuple[str, ...]:
    """Glob exclusion patterns matched against repo-relative paths."""
    return tuple(
        pattern
        for pattern in (*DEFAULT_EXCLUSIONS, *get_exclusions())
        if pattern and any(ch in pattern for ch in _MARKER_GLOB_CHARS)
    )


def _detect_marker_exists(project_root: Path, marker: str) -> bool:
    marker_text = str(marker).strip()
    if not marker_text:
        return False

    # Fast path for literal markers.
    if (project_root / marker_text).exists():
        return True

    # Wildcard markers (for example "*.fsproj") are matched at project root.
    if any(ch in marker_text for ch in _MARKER_GLOB_CHARS):
        return any(project_root.glob(marker_text))
    return False


def available_langs(
    *,
    refresh_registry: bool = False,
) -> list[str]:
    """Return list of registered language names."""
    if refresh_registry:
        _reset_dynamic_registries_for_refresh()
    load_all(force_reload=refresh_registry)
    return sorted(state.all_keys())


__all__ = [
    "auto_detect_lang",
    "available_langs",
    "get_lang",
    "make_lang_config",
]

"""Persisted exclusions must apply before language/state-path resolution.

Upstream #785: a scan could persist findings to the wrong language state
file when persisted exclusions changed language auto-detection. The state
path was resolved before ``set_exclusions`` ran, while the scan handler
detected the language after, so the two disagreed.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from desloppify.app.commands.helpers.lang import resolve_lang
from desloppify.app.commands.helpers.state import state_path
from desloppify.base.config import load_config
from desloppify.cli import _apply_persisted_exclusions, _load_shared_runtime


def _seed_mixed_project(root) -> None:
    """Two marker candidates; the cxx sources all live under excluded deps/."""
    (root / "package.json").write_text("{}")
    (root / "Makefile").write_text("all:\n")
    src = root / "src"
    src.mkdir()
    for index in range(3):
        (src / f"mod{index}.ts").write_text(f"export const v{index} = {index};\n")
    deps = root / "deps"
    deps.mkdir()
    for index in range(12):
        (deps / f"lib{index}.cpp").write_text("int f() { return 0; }\n")


def _write_exclusion_config(root) -> None:
    state_dir = root / ".desloppify"
    state_dir.mkdir()
    (state_dir / "config.json").write_text(json.dumps({"exclude": ["deps"]}))


def _scan_args() -> SimpleNamespace:
    return SimpleNamespace(
        command="scan", path=".", state=None, lang=None, exclude=None,
    )


def test_exclusions_flip_detection(set_project_root) -> None:
    """Fixture check: pre-exclusion detection differs from post-exclusion."""
    root = set_project_root
    _seed_mixed_project(root)
    args = _scan_args()

    assert state_path(args).name == "state-cxx.json"

    _apply_persisted_exclusions(args, {"exclude": ["deps"]})

    detected = resolve_lang(args)
    assert detected is not None
    assert detected.name == "typescript"


def test_load_shared_runtime_binds_post_exclusion_state(set_project_root) -> None:
    """main() applies persisted exclusions before resolving state path/lang."""
    root = set_project_root
    _seed_mixed_project(root)
    _write_exclusion_config(root)
    args = _scan_args()

    config = load_config()
    _apply_persisted_exclusions(args, config)
    _load_shared_runtime(args, config=config)

    detected = resolve_lang(args)
    assert detected is not None
    assert detected.name == "typescript"
    assert args.runtime.state_path.name == f"state-{detected.name}.json"

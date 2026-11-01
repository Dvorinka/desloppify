"""Tests for Rust detector phases."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from desloppify.base.discovery.paths import get_area
from desloppify.base.runtime_state import RuntimeContext, runtime_scope
from desloppify.languages.rust.phases import phase_coupling


def _write(tmp_path: Path, relpath: str, content: str) -> None:
    path = tmp_path / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_phase_coupling_does_not_emit_generic_cycles_for_rust_sibling_uses(tmp_path):
    _write(tmp_path, "Cargo.toml", "[package]\nname = 'demo-app'\nversion = '0.1.0'\n")
    _write(tmp_path, "src/main.rs", "mod foo;\nmod bar;\nfn main() {}\n")
    _write(tmp_path, "src/foo.rs", "use crate::bar::Bar;\npub struct Foo;\n")
    _write(tmp_path, "src/bar.rs", "use crate::foo::Foo;\npub struct Bar;\n")

    lang = SimpleNamespace(
        barrel_names={"lib.rs"},
        dep_graph=None,
        entry_patterns=["src/main.rs"],
        extensions=[".rs"],
        get_area=get_area,
        zone_map=None,
    )

    with runtime_scope(RuntimeContext(project_root=tmp_path)):
        issues, potentials = phase_coupling(tmp_path, lang)

    assert [issue for issue in issues if issue["detector"] == "cycles"] == []
    assert potentials["cycles"] == 0


def test_phase_coupling_treats_cargo_bin_path_as_entry(tmp_path):
    """#756: a [[bin]] path in Cargo.toml is an entry point, not an orphan."""
    _write(
        tmp_path,
        "Cargo.toml",
        '[package]\nname = "orphaned-bin-repro"\nversion = "0.1.0"\n\n'
        '[[bin]]\nname = "tool"\npath = "bin/tool.rs"\n',
    )
    _write(tmp_path, "src/lib.rs", "pub fn library_entry() {}\n")
    _write(
        tmp_path,
        "bin/tool.rs",
        'fn main() {\n    let items = [\n        "one",\n        "two",\n'
        '        "three",\n        "four",\n    ];\n\n'
        '    for item in items {\n        println!("{item}");\n    }\n}\n',
    )

    lang = SimpleNamespace(
        barrel_names={"lib.rs"},
        dep_graph=None,
        entry_patterns=["src/lib.rs", "src/main.rs", "src/bin/"],
        extensions=[".rs"],
        get_area=get_area,
        zone_map=None,
    )

    with runtime_scope(RuntimeContext(project_root=tmp_path)):
        issues, _potentials = phase_coupling(tmp_path, lang)

    orphaned = [i for i in issues if i["detector"] == "orphaned"]
    assert orphaned == []

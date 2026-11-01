"""Orphan-detector conventions: main guards, Django, Alembic, src layout."""

from __future__ import annotations

from pathlib import Path

from desloppify.engine.detectors.orphaned import (
    OrphanedDetectionOptions,
    detect_orphaned_files,
)
from desloppify.languages.python._helpers import py_has_main_guard
from desloppify.languages.python.detectors.deps import build_dep_graph

PAD = "\n".join(f"# pad {i}" for i in range(15)) + "\n"


def _graph(files: list[str]) -> dict:
    return {
        f: {"importer_count": 0, "import_count": 0, "importers": set()}
        for f in files
    }


def test_main_guard_file_is_not_orphaned(tmp_path):
    tool = tmp_path / "tool.py"
    tool.write_text(
        'import sys\n\nif __name__ == "__main__":\n    raise SystemExit(0)\n' + PAD
    )
    entries, _ = detect_orphaned_files(
        tmp_path,
        _graph([str(tool)]),
        [".py"],
        OrphanedDetectionOptions(entry_point_detector=py_has_main_guard),
    )
    assert entries == []


def test_py_has_main_guard_rejects_plain_modules(tmp_path):
    mod = tmp_path / "mod.py"
    mod.write_text("def f():\n    return 1\n")
    assert not py_has_main_guard(str(mod))


def test_django_conventions_not_orphaned(tmp_path):
    (tmp_path / "manage.py").write_text("# django\n")
    app = tmp_path / "core"
    app.mkdir()
    files = []
    for rel, content in {
        "core/urls.py": PAD,
        "core/admin_urls.py": PAD,
        "core/admin.py": PAD,
        "core/middleware.py": PAD,
        "core/templatetags/perms.py": PAD,
    }.items():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        files.append(str(target))
    live = tmp_path / "core" / "truly_dead.py"
    live.write_text(PAD)
    files.append(str(live))
    entries, _ = detect_orphaned_files(
        tmp_path, _graph(files), [".py"], OrphanedDetectionOptions()
    )
    assert [e["file"] for e in entries] == [str(live)]


def test_alembic_runtime_files_not_orphaned(tmp_path):
    (tmp_path / "alembic.ini").write_text(
        "[alembic]\nscript_location = %(here)s/alembic\n"
    )
    env = tmp_path / "alembic" / "env.py"
    version = tmp_path / "alembic" / "versions" / "0001_x.py"
    for f in (env, version):
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(PAD)
    entries, _ = detect_orphaned_files(
        tmp_path,
        _graph([str(env), str(version)]),
        [".py"],
        OrphanedDetectionOptions(),
    )
    assert entries == []


def test_src_layout_absolute_imports_resolve(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src" / "example"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    core = src / "core.py"
    core.write_text("def run():\n    return 1\n")
    cli = src / "cli.py"
    cli.write_text("from example.core import run\n")
    graph = build_dep_graph(tmp_path)
    assert str(cli) in graph[str(core)]["importers"]


def test_extract_skips_defs_inside_string_fixtures(tmp_path):
    from desloppify.languages.python.extractors import extract_py_functions

    mod = tmp_path / "selftest_mod.py"
    mod.write_text(
        '''def selftest():
    violating = \'\'\'
def _write(text, apply):
    write_without_read(text)
\'\'\'
    a = 1
    b = 2
    c = a + b
    return c


def real_helper(x):
    y = x + 1
    z = y * 2
    return z
'''
    )
    names = [fn.name for fn in extract_py_functions(str(mod))]
    assert "_write" not in names
    assert "real_helper" in names


def test_mixin_contract_excludes_inherited_methods(tmp_path):
    from desloppify.languages.python.detectors.coupling_contracts import (
        detect_implicit_mixin_contracts,
    )

    (tmp_path / "folders.py").write_text(
        '''
class FolderBaseMixin:
    def fetch_node(self):
        return 1
    def normalize_node(self):
        return 2
    def make_client(self):
        return 3

class FolderChildrenMixin(FolderBaseMixin):
    def list_children(self):
        return self.fetch_node() + self.normalize_node() + self.make_client()

class HostDependentMixin:
    def run(self):
        return self.provided_a() + self.provided_b() + self.provided_c()
'''
    )
    entries, _ = detect_implicit_mixin_contracts(tmp_path)
    assert [e["class"] for e in entries] == ["HostDependentMixin"]

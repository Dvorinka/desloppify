"""Missing-tool path for python unused detection (upstream issue #853)."""

from types import SimpleNamespace

from desloppify.languages.python.detectors import unused as unused_mod
from desloppify.languages.python import phases as py_phases


def _no_tools(monkeypatch):
    monkeypatch.setattr(unused_mod.shutil, "which", lambda _name: None)
    monkeypatch.setattr(unused_mod, "_module_available", lambda _name: False)


def test_detect_unused_returns_none_when_no_tool(monkeypatch, tmp_path):
    (tmp_path / "mod.py").write_text("import os\n")
    _no_tools(monkeypatch)
    entries, total = unused_mod.detect_unused(tmp_path)
    assert entries is None
    assert total == 1


def test_detect_unused_falls_back_to_pyflakes(monkeypatch, tmp_path):
    (tmp_path / "mod.py").write_text("import os\n")
    monkeypatch.setattr(unused_mod.shutil, "which", lambda _name: None)
    monkeypatch.setattr(
        unused_mod, "_module_available", lambda name: name == "pyflakes"
    )
    monkeypatch.setattr(
        unused_mod, "_try_pyflakes", lambda _path, _cat: [{"name": "os"}]
    )
    entries, _ = unused_mod.detect_unused(tmp_path)
    assert entries == [{"name": "os"}]


def test_phase_unused_reports_reduced_coverage(monkeypatch, tmp_path):
    (tmp_path / "mod.py").write_text("import os\n")
    _no_tools(monkeypatch)
    lang = SimpleNamespace(detector_coverage={}, coverage_warnings=[], zone_map=None)
    issues, signals = py_phases.phase_unused(tmp_path, lang)
    assert issues == []
    assert signals == {}
    assert lang.detector_coverage["unused"]["reason"] == "missing_tool"
    assert lang.coverage_warnings[0]["detector"] == "unused"

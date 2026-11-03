"""Nested function bodies must not inflate the enclosing function's cyclomatic count (#839)."""

from __future__ import annotations

from pathlib import Path

from desloppify.languages.typescript.detectors.smells import detect_smells


def _cycles(entries: list[dict]) -> list[tuple[int, str]]:
    return [
        (match["line"], match["content"])
        for entry in entries
        if entry["id"] == "high_cyclomatic_complexity"
        for match in entry["matches"]
    ]


def _write_project(tmp_path: Path, source: str) -> Path:
    (tmp_path / "sample.ts").write_text(source)
    return tmp_path


def test_nested_callback_branches_excluded_from_enclosing_function(tmp_path: Path):
    """Factory with three 5-branch arrow callbacks reports no finding (#839 repro)."""
    handlers = []
    for index in range(3):
        branches = "\n".join(
            f"    if (value === {branch}) return {branch};" for branch in range(5)
        )
        handlers.append(
            f"  const action{index} = (value: number) => {{\n"
            + branches
            + "\n    return -1;\n  };"
        )
    source = (
        "export function createActions() {\n"
        + "\n".join(handlers)
        + "\n  return [action0, action1, action2];\n}\n"
    )
    entries, _ = detect_smells(_write_project(tmp_path, source))
    assert _cycles(entries) == []


def test_function_with_own_branches_still_flagged(tmp_path: Path):
    """16 branches owned by the function itself still exceed the threshold."""
    branches = "\n".join(
        f"  if (v === {value}) return {value};" for value in range(16)
    )
    source = f"export function dense(v: number): number {{\n{branches}\n  return -1;\n}}\n"
    entries, _ = detect_smells(_write_project(tmp_path, source))
    cycles = _cycles(entries)
    assert len(cycles) == 1
    assert cycles[0][0] == 1


def test_complex_nested_function_flagged_on_itself(tmp_path: Path):
    """Complexity is not erased — a rich callback is counted on the callback."""
    branches = "\n".join(
        f"      if (v === {value}) return {value};" for value in range(16)
    )
    source = (
        "export function outer(v: number): number {\n"
        "  const inner = (v: number) => {\n"
        + branches
        + "\n    return -1;\n  };\n"
        "  return inner(v);\n}\n"
    )
    entries, _ = detect_smells(_write_project(tmp_path, source))
    cycles = _cycles(entries)
    assert len(cycles) == 1
    assert cycles[0][0] == 2
    assert cycles[0][1].startswith("inner()")

"""Tests for --diff PR review mode annotation mapping."""

from __future__ import annotations

import json

from desloppify.app.commands.scan.diff_annotations import (
    annotations_for_issues,
    changed_line_ranges,
    write_annotations_json,
)


def _issue(file: str, line: int | None, **kw) -> dict:
    issue = {
        "id": f"unused::{file}::name",
        "detector": "unused",
        "file": file,
        "status": "open",
        "tier": 2,
        "confidence": "high",
        "summary": "Unused import: foo",
        "detail": {},
    }
    if line is not None:
        issue["detail"]["line"] = line
    issue.update(kw)
    return issue


def _init_repo(path):
    import subprocess

    def run(*args):
        subprocess.run(args, cwd=path, check=True, capture_output=True, text=True)

    run("git", "init", "-b", "main")
    run("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "--allow-empty", "-m", "init")
    return run


def test_changed_line_ranges_parses_hunks(tmp_path):
    run = _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n" * 10)
    run("git", "add", ".")
    run("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "add")
    (tmp_path / "a.py").write_text("x = 1\n" * 3 + "y = 2\n" * 4 + "x = 1\n" * 3)
    run("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-am", "change")
    ranges = changed_line_ranges("HEAD~1", cwd=tmp_path)
    assert ranges == {"a.py": [(4, 7)]}


def test_annotations_filter_to_changed_lines():
    ranges = {"src/a.py": [(10, 20)], "src/b.py": [(1, 3)]}
    issues = [
        _issue("src/a.py", 15),            # in range -> annotated
        _issue("src/a.py", 50),            # changed file, unchanged line -> skip
        _issue("src/b.py", None),          # no line on changed file -> included
        _issue("src/c.py", 5),             # untouched file -> skip
        _issue("src/a.py", 12, status="fixed"),  # closed -> skip
    ]
    anns = annotations_for_issues(issues, ranges)
    assert [(a["file"], a["line"]) for a in anns] == [
        ("src/a.py", 15),
        ("src/b.py", None),
    ]


def test_write_annotations_json(tmp_path):
    out = tmp_path / "ann.json"
    write_annotations_json(
        out,
        [{"file": "a.py", "line": 3, "summary": "x", "detector": "unused"}],
        base="main",
        prev_strict=80.0,
        new_strict=82.5,
    )
    payload = json.loads(out.read_text())
    assert payload["strict_delta"] == 2.5
    assert payload["annotations"][0]["line"] == 3

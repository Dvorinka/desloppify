"""Direct tests for matched_ignore_pattern tail-component matching (#940).

Issue IDs can carry a trailing ::line/::detail component. A documented
suppression glob like ``detector::*::rule`` must still match those IDs —
previously it only worked when the ID had no tail, so recorded patterns
silently filtered nothing.
"""

from __future__ import annotations

from desloppify.engine._state.filtering import matched_ignore_pattern


def _match(issue_id: str, file: str, patterns: list[str]) -> str | None:
    return matched_ignore_pattern(issue_id, file, patterns)


def test_rule_glob_matches_id_with_line_suffix() -> None:
    issue_id = "unused::packages/xjvm/bench/steps.lua::unused_import::6"
    pattern = "unused::*::unused_import"
    assert _match(issue_id, "packages/xjvm/bench/steps.lua", [pattern]) == pattern


def test_rule_glob_still_matches_id_without_suffix() -> None:
    issue_id = "orphaned::src/a.py::helper"
    pattern = "orphaned::*::helper"
    assert _match(issue_id, "src/a.py", [pattern]) == pattern


def test_explicit_tail_glob_still_works() -> None:
    issue_id = "unused::a.lua::unused_import::6"
    pattern = "unused::*::unused_import::*"
    assert _match(issue_id, "a.lua", [pattern]) == pattern


def test_rule_glob_does_not_match_other_rules() -> None:
    issue_id = "unused::a.lua::other_rule::6"
    assert _match(issue_id, "a.lua", ["unused::*::unused_import"]) is None


def test_rule_glob_does_not_match_other_detectors() -> None:
    issue_id = "deps::a.lua::unused_import::6"
    assert _match(issue_id, "a.lua", ["unused::*::unused_import"]) is None


def test_file_globs_unaffected() -> None:
    assert (
        _match("det::src/a.py::x::1", "src/a.py", ["src/*"]) == "src/*"
    )
    assert _match("det::src/a.py::x::1", "src/a.py", ["other/*"]) is None


def test_non_glob_id_prefix_unchanged() -> None:
    issue_id = "unused::src/a.py::name::7"
    assert _match(issue_id, "src/a.py", ["unused::src/a.py"]) == "unused::src/a.py"
    assert _match(issue_id, "src/a.py", ["deps::src/a.py"]) is None

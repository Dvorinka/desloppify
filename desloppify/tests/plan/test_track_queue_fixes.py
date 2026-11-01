"""Regression tests for TRACK-queue machinery fixes.

Covers upstream issues #906, #919, #928/#929, #930, #931/#701.
"""

from __future__ import annotations

import pytest

from desloppify.engine._plan.operations.cluster import add_to_cluster, create_cluster
from desloppify.engine._plan.step_completion import auto_complete_steps
from desloppify.engine._work_queue.snapshot import (
    _Partitions,
    _build_backlog,
    build_queue_snapshot,
)


def _assessment_item(fid: str) -> dict:
    return {
        "id": fid,
        "detector": "subjective_assessment",
        "file": fid,
        "tier": 3,
        "confidence": "high",
        "summary": f"assessment {fid}",
        "status": "open",
        "detail": {},
        "work_item_kind": "assessment_request",
    }


def _objective_item(fid: str) -> dict:
    return {
        "id": fid,
        "detector": "unused",
        "file": "test.py",
        "tier": 1,
        "confidence": "high",
        "summary": f"issue {fid}",
        "status": "open",
        "detail": {},
    }


# ── #906: skipped assessments must not select an empty postflight phase ──────


def test_skipped_assessment_request_not_in_postflight_partition() -> None:
    state = {
        "work_items": {
            "subjective::mid_level_elegance": _assessment_item(
                "subjective::mid_level_elegance"
            ),
            "unused::test.py::a": _objective_item("unused::test.py::a"),
        },
        "dimension_scores": {},
        "scan_path": "/tmp/test",
    }
    plan = {
        "version": 1,
        "queue_order": ["unused::test.py::a"],
        "skipped": {
            "subjective::mid_level_elegance": {"kind": "temporary"},
        },
        "clusters": {},
        "refresh_state": {"lifecycle_phase": "plan"},
        "plan_start_scores": {"strict": 50.0},
    }
    snapshot = build_queue_snapshot(state, plan=plan)
    exec_ids = {item.get("id") for item in snapshot.execution_items}
    backlog_ids = {item.get("id") for item in snapshot.backlog_items}
    assert "subjective::mid_level_elegance" not in exec_ids
    assert "subjective::mid_level_elegance" not in backlog_ids
    # The skipped assessment must not select a phase that empties the queue.
    assert snapshot.phase != "assessment_postflight"


def test_skipped_review_finding_not_in_postflight_partition() -> None:
    review_item = {
        "id": "review::test.py::naming",
        "detector": "review",
        "file": "test.py",
        "tier": 3,
        "confidence": "high",
        "summary": "review finding",
        "status": "open",
        "detail": {"dimension": "naming_quality"},
        "work_item_kind": "review_defect",
    }
    state = {
        "work_items": {
            "review::test.py::naming": review_item,
            "unused::test.py::a": _objective_item("unused::test.py::a"),
        },
        "dimension_scores": {},
        "scan_path": "/tmp/test",
    }
    plan = {
        "version": 1,
        "queue_order": ["unused::test.py::a", "review::test.py::naming"],
        "skipped": {
            "review::test.py::naming": {"kind": "temporary"},
        },
        "clusters": {},
        "plan_start_scores": {"strict": 50.0},
    }
    snapshot = build_queue_snapshot(state, plan=plan)
    all_ids = {
        item.get("id")
        for item in (*snapshot.execution_items, *snapshot.backlog_items)
    }
    assert "review::test.py::naming" not in all_ids


# ── #928/#929: backlog lists each canonical ID once ──────────────────────────


def test_backlog_dedupes_ids_across_partitions() -> None:
    dup_a = {"id": "test_coverage::x::a", "kind": "issue"}
    dup_b = {"id": "test_coverage::x::b", "kind": "issue"}
    partitions = _Partitions(
        objective_items=[dict(dup_a), dict(dup_b)],
        explicit_objective_items=[],
        review_issue_items=[dict(dup_a)],  # same id in a second partition
        initial_review_items=[],
        subjective_postflight_items=[],
        postflight_assessment_items=[dict(dup_b)],  # and a third
        postflight_review_items=[],
        scan_items=[],
        postflight_workflow_items=[],
        triage_items=[],
        explicit_queue_items=[],
        anchored_execution_items=[],
    )
    backlog = _build_backlog(partitions, set())
    ids = [item["id"] for item in backlog]
    assert sorted(ids) == ["test_coverage::x::a", "test_coverage::x::b"]


# ── #930: cluster add refuses skipped IDs instead of crashing ────────────────


def test_add_to_cluster_rejects_skipped_ids() -> None:
    plan = {
        "version": 1,
        "queue_order": [],
        "clusters": {},
        "skipped": {"unused::a.py::x": {"kind": "permanent"}},
        "overrides": {},
    }
    create_cluster(plan, "example")
    with pytest.raises(ValueError, match="unskip"):
        add_to_cluster(plan, "example", ["unused::a.py::x", "unused::b.py::y"])
    # No partial mutation before the refusal.
    assert plan["clusters"]["example"]["issue_ids"] == []
    assert "unused::a.py::x" not in plan["queue_order"]


def test_add_to_cluster_accepts_unskipped_ids() -> None:
    plan = {
        "version": 1,
        "queue_order": [],
        "clusters": {},
        "skipped": {"unused::a.py::x": {"kind": "permanent"}},
        "overrides": {},
    }
    create_cluster(plan, "example")
    count = add_to_cluster(plan, "example", ["unused::b.py::y"])
    assert count == 1
    assert plan["clusters"]["example"]["issue_ids"] == ["unused::b.py::y"]


# ── #931/#701: open findings outside the queue keep their steps pending ─────


def test_step_stays_pending_when_ref_open_in_state() -> None:
    plan = {
        "queue_order": [],
        "clusters": {
            "inventory": {
                "issue_ids": [],
                "action_steps": [
                    {
                        "title": "Inspect coverage evidence",
                        "done": False,
                        "issue_refs": ["test_coverage::src/example.ts::untested_module"],
                    }
                ],
            },
        },
    }
    issues = {
        "test_coverage::src/example.ts::untested_module": {
            "status": "open",
        }
    }
    assert auto_complete_steps(plan, issues=issues) == []
    step = plan["clusters"]["inventory"]["action_steps"][0]
    assert step["done"] is False


def test_step_completes_when_ref_resolved_in_state() -> None:
    plan = {
        "queue_order": [],
        "clusters": {
            "inventory": {
                "issue_ids": [],
                "action_steps": [
                    {
                        "title": "Inspect coverage evidence",
                        "done": False,
                        "issue_refs": ["test_coverage::src/example.ts::untested_module"],
                    }
                ],
            },
        },
    }
    issues = {
        "test_coverage::src/example.ts::untested_module": {
            "status": "fixed",
        }
    }
    messages = auto_complete_steps(plan, issues=issues)
    assert len(messages) == 1
    assert plan["clusters"]["inventory"]["action_steps"][0]["done"] is True


def test_step_completion_without_issues_keeps_legacy_behavior() -> None:
    plan = {
        "queue_order": [],
        "clusters": {
            "inventory": {
                "issue_ids": [],
                "action_steps": [
                    {
                        "title": "Legacy",
                        "done": False,
                        "issue_refs": ["gone"],
                    }
                ],
            },
        },
    }
    assert len(auto_complete_steps(plan)) == 1


# ── #780: --state must load the sibling plan, not the default project plan ───


def test_load_plan_for_runtime_uses_state_sibling(tmp_path, monkeypatch) -> None:
    from desloppify.app.commands.next import cmd as next_cmd

    seen: list[object] = []

    class _Runtime:
        state_path = tmp_path / "browser" / "state-javascript.json"

    monkeypatch.setattr(next_cmd, "load_plan", lambda p=None: seen.append(p) or {})
    next_cmd._load_plan_for_runtime(_Runtime())
    assert seen == [tmp_path / "browser" / "plan.json"]


def test_load_plan_for_runtime_default_without_state_path(monkeypatch) -> None:
    from desloppify.app.commands.next import cmd as next_cmd

    seen: list[object] = []

    class _Runtime:
        state_path = None

    monkeypatch.setattr(next_cmd, "load_plan", lambda p=None: seen.append(p) or {})
    next_cmd._load_plan_for_runtime(_Runtime())
    assert seen == [None]


# ── #727: auto-detect file counting honors configured exclusions ────────────


def test_scannable_file_count_skips_excluded_dirs(tmp_path) -> None:
    from desloppify.languages._framework.registry import resolution
    from desloppify.base.discovery import source as source_mod

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.cs").write_text("class A {}")
    (tmp_path / "packages").mkdir()
    for i in range(10):
        (tmp_path / "packages" / f"h{i}.h").write_text("#pragma once")

    class _Cfg:
        def file_finder(self, root):
            return sorted(str(p) for p in root.rglob("*") if p.is_file())

    monkey_excl = source_mod.resolve_runtime_context()
    old = monkey_excl.exclusions
    try:
        monkey_excl.exclusions = ("packages",)
        assert resolution._scannable_file_count(_Cfg(), tmp_path) == 1
        # Without the exclusion the vendored headers dominate the count.
        monkey_excl.exclusions = ()
        assert resolution._scannable_file_count(_Cfg(), tmp_path) == 11
    finally:
        monkey_excl.exclusions = old


def test_scannable_file_count_skips_glob_exclusions(tmp_path) -> None:
    from desloppify.languages._framework.registry import resolution
    from desloppify.base.discovery import source as source_mod

    (tmp_path / "gen").mkdir()
    (tmp_path / "gen" / "a.gen.cs").write_text("class G {}")
    (tmp_path / "b.cs").write_text("class B {}")

    class _Cfg:
        def file_finder(self, root):
            return sorted(str(p) for p in root.rglob("*.cs") if p.is_file())

    ctx = source_mod.resolve_runtime_context()
    old = ctx.exclusions
    try:
        ctx.exclusions = ("gen/*.gen.cs",)
        assert resolution._scannable_file_count(_Cfg(), tmp_path) == 1
    finally:
        ctx.exclusions = old

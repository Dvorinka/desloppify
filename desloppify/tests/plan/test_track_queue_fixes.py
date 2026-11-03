"""Regression tests for TRACK-queue machinery fixes.

Covers upstream issues #906, #919, #928/#929, #930, #931/#701.
"""

from __future__ import annotations

import pytest

from desloppify.engine._plan.operations.cluster import add_to_cluster, create_cluster
from desloppify.engine._plan.step_completion import auto_complete_steps
from desloppify.engine._work_queue.snapshot import (
    _build_backlog,
    _Partitions,
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
    from desloppify.base.discovery import source as source_mod
    from desloppify.languages._framework.registry import resolution

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
    from desloppify.base.discovery import source as source_mod
    from desloppify.languages._framework.registry import resolution

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


# ── #888 part 2: queued mechanical work must not be masked by the ────────────
#    stale-assessment postflight (subjective/objective queue deadlock)


def test_queued_mechanical_work_precedes_stale_assessment_postflight() -> None:
    """#888: `next` shows the planned cluster, not the gated stale review."""
    state = {
        "work_items": {
            "smells::src/a.py::1": {
                "id": "smells::src/a.py::1",
                "detector": "smells",
                "file": "src/a.py",
                "tier": 2,
                "confidence": "high",
                "summary": "mech 1",
                "status": "open",
                "detail": {},
            },
            "smells::src/b.py::2": {
                "id": "smells::src/b.py::2",
                "detector": "smells",
                "file": "src/b.py",
                "tier": 2,
                "confidence": "high",
                "summary": "mech 2",
                "status": "open",
                "detail": {},
            },
            "smells::src/c.py::3": {
                "id": "smells::src/c.py::3",
                "detector": "smells",
                "file": "src/c.py",
                "tier": 2,
                "confidence": "high",
                "summary": "mech 3",
                "status": "open",
                "detail": {},
            },
        },
        "scan_count": 5,
        "scan_path": ".",
        "dimension_scores": {
            "Error consistency": {
                "score": 65.0,
                "strict": 65.0,
                "failing": 1,
                "detectors": {
                    "subjective_assessment": {"dimension_key": "error_consistency"},
                },
            },
        },
        "subjective_assessments": {
            "error_consistency": {
                "score": 65.0,
                "source": "holistic",
                "assessed_at": "2026-01-01T11:00:00+00:00",
                "needs_review_refresh": True,
                "stale_since": "2026-01-01T00:00:00+00:00",
            },
        },
        "last_scan": "2026-01-01T10:00:00+00:00",
    }
    plan = {
        "version": 1,
        "queue_order": [
            "smells::src/a.py::1",
            "smells::src/b.py::2",
            "smells::src/c.py::3",
        ],
        "clusters": {
            "test-coverage": {
                "name": "test-coverage",
                "auto": False,
                "issue_ids": [
                    "smells::src/a.py::1",
                    "smells::src/b.py::2",
                    "smells::src/c.py::3",
                ],
                "description": "Test coverage findings",
                "user_modified": True,
            },
        },
        "refresh_state": {},
        "epic_triage_meta": {
            "triaged_ids": [
                "smells::src/a.py::1",
                "smells::src/b.py::2",
                "smells::src/c.py::3",
            ],
        },
    }

    snapshot = build_queue_snapshot(state, plan=plan)
    exec_ids = [item.get("id") for item in snapshot.execution_items]
    # The planned mechanical work is the actionable front; the stale
    # assessment marker stays visible behind it instead of masking the
    # queue (the review rerun gate blocks on that open objective backlog,
    # so review-first ordering deadlocked next ↔ review preflight).
    assert snapshot.phase == "assessment"
    assert exec_ids[:3] == [
        "smells::src/a.py::1",
        "smells::src/b.py::2",
        "smells::src/c.py::3",
    ]
    assert "subjective::error_consistency" in exec_ids

    # Plan-order collapse (what `next` and the resolve queue guard render):
    # the manual cluster fronts the queue ahead of the stale review.
    from desloppify.engine._work_queue.plan_order import collapse_clusters

    collapsed_ids = [item.get("id") for item in collapse_clusters(list(snapshot.execution_items), plan)]
    assert collapsed_ids[:2] == ["test-coverage", "subjective::error_consistency"]


def test_assessment_postflight_without_queued_execution_keeps_partition() -> None:
    """No planned execution → the assessment phase queue stays exclusive."""
    state = {
        "work_items": {
            "smells::src/a.py::1": {
                "id": "smells::src/a.py::1",
                "detector": "smells",
                "file": "src/a.py",
                "tier": 2,
                "confidence": "high",
                "summary": "mech 1",
                "status": "open",
                "detail": {},
            },
        },
        "scan_count": 5,
        "scan_path": ".",
        "subjective_assessments": {
            "error_consistency": {
                "score": 65.0,
                "source": "holistic",
                "assessed_at": "2026-01-01T11:00:00+00:00",
                "needs_review_refresh": True,
                "stale_since": "2026-01-01T00:00:00+00:00",
            },
        },
        "dimension_scores": {
            "Error consistency": {
                "score": 65.0,
                "strict": 65.0,
                "failing": 1,
                "detectors": {
                    "subjective_assessment": {"dimension_key": "error_consistency"},
                },
            },
        },
        "last_scan": "2026-01-01T10:00:00+00:00",
    }
    plan = {"version": 1, "queue_order": [], "clusters": {}, "refresh_state": {}}

    snapshot = build_queue_snapshot(state, plan=plan)
    exec_ids = [item.get("id") for item in snapshot.execution_items]
    assert exec_ids == ["subjective::error_consistency"]


# ── #900: strategist work must match current schemas ─────────────────────────


def test_strategy_items_are_live_queue_work() -> None:
    """#900: queued strategy::* work items surface in `next`, not 0 items."""
    state = {
        "work_items": {
            "strategy::consolidate-coverage": {
                "id": "strategy::consolidate-coverage",
                "detector": "strategy",
                "file": ".",
                "tier": 2,
                "priority": "high",
                "summary": "Consolidate coverage clusters",
                "status": "open",
                "detail": {"dimension": "unknown", "source": "strategist"},
            },
        },
        "issues": {},
        "scan_count": 5,
        "scan_path": ".",
        "last_scan": "2026-01-01T10:00:00+00:00",
    }
    plan = {
        "version": 1,
        "queue_order": ["strategy::consolidate-coverage"],
        "clusters": {},
        "refresh_state": {},
        "epic_triage_meta": {"triaged_ids": ["strategy::consolidate-coverage"]},
    }

    snapshot = build_queue_snapshot(state, plan=plan)
    exec_ids = [item.get("id") for item in snapshot.execution_items]
    assert "strategy::consolidate-coverage" in exec_ids


def test_unenriched_clusters_ignores_completed_clusters() -> None:
    """#900: enrichment gates only clusters that can still execute."""
    from desloppify.app.commands.plan.triage.stages.helpers import (
        unenriched_clusters,
    )

    plan = {
        "version": 1,
        "queue_order": ["smells::a.py::1"],
        "clusters": {
            "done-batch": {
                "name": "done-batch",
                "auto": False,
                "issue_ids": ["smells::old.py::9"],
                "execution_status": "done",
            },
            "live-batch": {
                "name": "live-batch",
                "auto": False,
                "issue_ids": ["smells::a.py::1"],
            },
        },
        "refresh_state": {},
    }
    gaps = dict(unenriched_clusters(plan))
    assert "done-batch" not in gaps
    assert gaps["live-batch"] == ["description", "action_steps"]


def test_masked_review_findings_do_not_suppress_subjective_dims() -> None:
    """#813: a stale-triage-hidden review finding must not empty `next`."""
    state = {
        "work_items": {
            "review::src/x.py::1": {
                "id": "review::src/x.py::1",
                "detector": "review",
                "status": "open",
                "file": "src/x.py",
                "confidence": "high",
                "detail": {"dimension": "logic_clarity"},
            },
        },
        "issues": {},
        "scan_count": 81,
        "scan_path": ".",
        "last_scan": "2026-01-01T10:00:00+00:00",
        "subjective_assessments": {
            "logic_clarity": {
                "score": 80.0,
                "needs_review_refresh": True,
                "stale_since": "2026-01-01T00:00:00+00:00",
                "refresh_reason": "mechanical_issues_changed",
            },
        },
        "dimension_scores": {
            "Logic clarity": {
                "score": 80.0,
                "strict": 80.0,
                "failing": 0,
                "detectors": {
                    "subjective_assessment": {"dimension_key": "logic_clarity"},
                },
            },
        },
    }
    state["issues"] = dict(state["work_items"])
    plan = {
        "version": 1,
        "queue_order": ["subjective::logic_clarity"],
        "clusters": {},
        "refresh_state": {
            "lifecycle_phase": "plan",
            "subjective_review_completed_at_scan_count": 80,
            "postflight_scan_completed_at_scan_count": 81,
        },
    }
    # Triage has never run, so the covering review finding is masked — the
    # dim item is the only visible path and must stay in the queue.
    snapshot = build_queue_snapshot(state, plan=plan)
    exec_ids = [item.get("id") for item in snapshot.execution_items]
    assert "subjective::logic_clarity" in exec_ids

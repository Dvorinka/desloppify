"""Direct integration tests for scan workflow runtime + merge paths."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from desloppify import state as state_mod
from desloppify.app.commands.helpers.command_runtime import CommandRuntime
from desloppify.app.commands.scan.workflow import (
    ScanRuntime,
    ScanStateContractError,
    merge_scan_results,
    prepare_scan_runtime,
)
from desloppify.base.runtime_state import RuntimeContext, runtime_scope
from desloppify.base.discovery.file_paths import rel
from desloppify.engine.plan_state import empty_plan, load_plan, save_plan
from desloppify.languages._framework.frameworks.detection import (
    detect_ecosystem_frameworks,
)
from desloppify.languages._framework.frameworks.specs.nextjs import _nextjs_info
from desloppify.languages._framework.runtime_support.runtime import (
    LangRunOverrides,
    make_lang_run,
)
from desloppify.languages.typescript import TypeScriptConfig


def test_prepare_scan_runtime_uses_real_runtime_and_resets_subjective(tmp_path):
    state = {
        "subjective_assessments": {
            "naming_quality": {
                "score": 97.0,
                "source": "manual_override",
                "provisional_override": True,
                "provisional_until_scan": 2,
            }
        }
    }
    config = {
        "zone_overrides": {"src/foo.py": "test"},
    }
    runtime = CommandRuntime(
        config=config,
        state=state,
        state_path=tmp_path / "state.json",
    )
    args = SimpleNamespace(
        path=str(tmp_path),
        runtime=runtime,
        lang=None,
        reset_subjective=True,
        skip_slow=False,
        profile=None,
    )

    scan_runtime = prepare_scan_runtime(args)

    assert scan_runtime.state_path == tmp_path / "state.json"
    assert scan_runtime.path == tmp_path
    assert scan_runtime.profile == "full"
    assert scan_runtime.effective_include_slow is True
    assert scan_runtime.zone_overrides == {"src/foo.py": "test"}
    assert scan_runtime.reset_subjective_count >= 10
    naming = scan_runtime.state["subjective_assessments"]["naming_quality"]
    assert naming["score"] == 0.0
    assert naming["source"] == "scan_reset_subjective"
    assert naming["reset_by"] == "scan_reset_subjective"


def test_prepare_scan_runtime_rejects_file_scan_path(tmp_path):
    scan_target = tmp_path / "src.rs"
    scan_target.write_text("fn main() {}\n", encoding="utf-8")
    runtime = CommandRuntime(config={}, state={}, state_path=tmp_path / "state.json")
    args = SimpleNamespace(
        path=str(scan_target),
        runtime=runtime,
        lang=None,
        reset_subjective=False,
        skip_slow=False,
        profile=None,
    )

    try:
        prepare_scan_runtime(args)
    except ScanStateContractError as exc:
        assert "scan --path must point to an existing directory" in str(exc)
        assert str(scan_target) in str(exc)
    else:  # pragma: no cover - assertion branch
        raise AssertionError("expected file scan path to be rejected")


def test_merge_scan_results_persists_state_and_reconciles_plan(tmp_path):
    state_path = tmp_path / "state.json"
    plan_path = tmp_path / "plan.json"
    stale_id = "structural::src/legacy.py::legacy_large_file"

    plan = empty_plan()
    plan["queue_order"] = [stale_id]
    save_plan(plan, plan_path)

    state = state_mod.empty_state()
    state["scan_path"] = rel(str(tmp_path))
    state_mod.save_state(state, state_path)
    # save_state recomputes scores from issues — stamp the prior snapshot
    # directly so the merge reads a realistic previous score.
    import json as _json

    persisted = _json.loads(state_path.read_text())
    persisted["strict_score"] = 82.5
    persisted["overall_score"] = 84.0
    persisted["objective_score"] = 86.0
    persisted["verified_strict_score"] = 82.5
    # Mark the state as scan-sourced so load_state does not attempt plan
    # reconstruction (the test plan file carries a queue order).
    persisted["last_scan"] = "2026-10-31T00:00:00Z"
    state_path.write_text(_json.dumps(persisted))

    runtime = ScanRuntime(
        args=SimpleNamespace(force_resolve=False),
        state_path=state_path,
        state=state,
        path=tmp_path,
        config={
            "ignore": [],
            "needs_rescan": False,
            "holistic_max_age_days": 30,
        },
        lang=None,
        lang_label="",
        profile="full",
        effective_include_slow=True,
        zone_overrides=None,
    )

    issues = [
        state_mod.make_issue(
            "structural",
            "src/new_module.py",
            "new_large_file",
            tier=2,
            confidence="high",
            summary="Large module should be split",
            detail={"loc": 260},
        )
    ]

    merge = merge_scan_results(
        runtime,
        issues,
        potentials={"structural": 1},
        codebase_metrics={"total_files": 1},
    )

    assert merge.prev_strict == 82.5
    assert merge.diff.get("new", 0) >= 1

    persisted = state_mod.load_state(state_path)
    assert persisted["scan_path"] == rel(str(tmp_path))
    assert issues[0]["id"] in persisted["issues"]

    plan_after = load_plan(plan_path)
    assert stale_id not in plan_after.get("queue_order", [])
    assert stale_id in plan_after.get("superseded", {})
    plan_start = plan_after.get("plan_start_scores", {})
    assert isinstance(plan_start.get("strict"), float)


def test_merge_scan_results_preserves_external_state_changes(tmp_path):
    """A concurrent command's write between load and merge must not be lost."""
    state_path = tmp_path / "state.json"

    state = state_mod.empty_state()
    state["scan_path"] = rel(str(tmp_path))
    state_mod.save_state(state, state_path)

    runtime = ScanRuntime(
        args=SimpleNamespace(force_resolve=False),
        state_path=state_path,
        state=state_mod.load_state(state_path),
        path=tmp_path,
        config={"ignore": [], "needs_rescan": False},
        lang=None,
        lang_label="",
        profile="full",
        effective_include_slow=True,
        zone_overrides=None,
    )

    # Simulate another command mutating state after this scan loaded it.
    with state_mod.state_lock(state_path) as state:
        state["work_items"]["external::src/x.py::1"] = {"status": "fixed"}

    issues = [
        state_mod.make_issue(
            "structural",
            "src/new_module.py",
            "new_large_file",
            tier=2,
            confidence="high",
            summary="Large module should be split",
            detail={"loc": 260},
        )
    ]
    merge_scan_results(
        runtime,
        issues,
        potentials={"structural": 1},
        codebase_metrics={"total_files": 1},
    )

    persisted = state_mod.load_state(state_path)
    assert issues[0]["id"] in persisted["issues"]
    assert persisted["work_items"]["external::src/x.py::1"]["status"] == "fixed"


def test_merge_scan_results_serializes_concurrent_merges(tmp_path):
    """Two concurrent merges must not clobber each other's non-scan fields."""
    import threading

    state_path = tmp_path / "state.json"
    state = state_mod.empty_state()
    state["scan_path"] = rel(str(tmp_path))
    state_mod.save_state(state, state_path)

    def _make_runtime() -> ScanRuntime:
        return ScanRuntime(
            args=SimpleNamespace(force_resolve=False),
            state_path=state_path,
            state=state_mod.load_state(state_path),
            path=tmp_path,
            config={"ignore": [], "needs_rescan": False},
            lang=None,
            lang_label="",
            profile="full",
            effective_include_slow=True,
            zone_overrides=None,
        )

    barrier = threading.Barrier(2)
    errors: list[BaseException] = []
    expected_ids: list[str] = []

    def _merge(name: str) -> None:
        try:
            barrier.wait(timeout=10)
            issue = state_mod.make_issue(
                "structural",
                f"src/{name}.py",
                f"{name}_issue",
                tier=2,
                confidence="high",
                summary=f"{name} issue",
                detail={"loc": 260},
            )
            expected_ids.append(issue["id"])
            merge_scan_results(
                _make_runtime(),
                [issue],
                potentials={"structural": 1},
                codebase_metrics={"total_files": 1},
            )
        except BaseException as exc:  # noqa: BLE001 - surface thread failures
            errors.append(exc)

    threads = [
        threading.Thread(target=_merge, args=(f"mod{i}",)) for i in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert not errors
    persisted = state_mod.load_state(state_path)
    ids = set(persisted["issues"])
    for issue_id in expected_ids:
        assert issue_id in ids


def test_framework_runtime_cache_stays_out_of_persisted_review_cache(tmp_path: Path):
    state_path = tmp_path / "state.json"
    (tmp_path / "package.json").write_text(
        '{"dependencies":{"next":"15.0.0"},"scripts":{"build":"next build"}}\n'
    )
    (tmp_path / "next.config.ts").write_text("export default {};\n")
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "page.tsx").write_text("export default function Page() { return null; }\n")

    state = state_mod.empty_state()
    review_cache: dict[str, object] = {}
    state["review_cache"] = review_cache
    lang = make_lang_run(
        TypeScriptConfig(),
        overrides=LangRunOverrides(review_cache=review_cache),
    )

    with runtime_scope(RuntimeContext(project_root=tmp_path)):
        detection = detect_ecosystem_frameworks(tmp_path, lang, "node")
        info = _nextjs_info(tmp_path, lang)
        state_mod.save_state(state, state_path)

    assert "nextjs" in detection.present
    assert info.package_root == tmp_path
    assert state["review_cache"] == {}
    assert any(key.startswith("frameworks.ecosystem.present:node:") for key in lang.runtime_cache)
    assert any(key.startswith("framework.nextjs.info:") for key in lang.runtime_cache)

    persisted = state_mod.load_state(state_path)
    assert persisted.get("review_cache", {}) == {}

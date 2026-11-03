"""Tests for --batch-mode grouped/single batch granularity selection."""

from __future__ import annotations

from pathlib import Path

from desloppify.app.commands.review.batch.grouping import (
    batch_mode_for_args,
    resolve_batch_mode,
    select_batches_for_run,
)
from desloppify.app.commands.review.batch.prompt_template import render_batch_prompt
from desloppify.app.commands.review.batches_runtime import (
    BatchRunSummaryConfig,
    write_run_summary,
)
from desloppify.intelligence.review.prepare_batches_collectors import (
    _DIMENSION_FILE_MAPPING,
)


def _dim_batches(dims: list[str]) -> list[dict]:
    return [
        {
            "name": dim,
            "dimensions": [dim],
            "why": f"{dim} review",
            "persona": f"persona-{dim}",
        }
        for dim in dims
    ]


def test_resolve_batch_mode_defaults_and_normalizes():
    assert resolve_batch_mode(None) == "per-dimension"
    assert resolve_batch_mode("bogus") == "per-dimension"
    assert resolve_batch_mode("GROUPED") == "grouped"
    assert resolve_batch_mode(" single ") == "single"
    assert batch_mode_for_args(object()) == "per-dimension"

    class _Args:
        batch_mode = "single"

    assert batch_mode_for_args(_Args()) == "single"


def test_per_dimension_mode_returns_exploded_batches():
    dims = ["convention_outlier", "error_consistency", "abstraction_fitness"]
    out = select_batches_for_run(_dim_batches(dims), mode="per-dimension")
    assert [b["dimensions"] for b in out] == [[d] for d in dims]


def test_grouped_mode_merges_dimensions_by_collector():
    dims = [
        "convention_outlier",
        "error_consistency",
        "naming_quality",
        "cross_module_architecture",
        "test_strategy",
        "api_surface_coherence",
    ]
    out = select_batches_for_run(_dim_batches(dims), mode="grouped")
    names = [b["name"] for b in out]
    assert names == ["conventions", "arch_coupling", "testing_api"]
    by_name = {b["name"]: b for b in out}
    assert by_name["conventions"]["dimensions"] == [
        "convention_outlier",
        "error_consistency",
        "naming_quality",
    ]
    assert by_name["testing_api"]["dimensions"] == [
        "test_strategy",
        "api_surface_coherence",
    ]


def test_grouped_mode_covers_all_dimensions_exactly_once():
    dims = sorted(_DIMENSION_FILE_MAPPING)
    out = select_batches_for_run(_dim_batches(dims), mode="grouped")
    covered = [dim for batch in out for dim in batch["dimensions"]]
    assert sorted(covered) == dims
    assert len(out) == len(set(_DIMENSION_FILE_MAPPING.values()))


def test_single_mode_merges_all_into_one_batch():
    dims = ["convention_outlier", "error_consistency", "naming_quality"]
    out = select_batches_for_run(_dim_batches(dims), mode="single")
    assert len(out) == 1
    batch = out[0]
    assert batch["name"] == "all_dimensions"
    assert batch["dimensions"] == dims
    # persona survives from the first member
    assert batch["persona"] == "persona-convention_outlier"


def test_merge_preserves_prompts_counts_signals_and_focus():
    batches = [
        {
            "name": "convention_outlier",
            "dimensions": ["convention_outlier"],
            "dimension_prompts": {"convention_outlier": {"description": "d1"}},
            "judgment_finding_counts": {"dup": 2},
            "mechanical_finding_counts": {"large_file": 3},
            "files_to_read": ["a.py", "b.py"],
            "historical_issue_focus": {
                "dimensions": ["convention_outlier"],
                "max_items": 5,
                "selected_count": 1,
                "issues": [{"dimension": "convention_outlier", "identifier": "i1"}],
            },
        },
        {
            "name": "error_consistency",
            "dimensions": ["error_consistency"],
            "dimension_prompts": {"error_consistency": {"description": "d2"}},
            "judgment_finding_counts": {"dup": 4},
            "concern_signals": [{"type": "t", "file": "x.py", "fingerprint": "f"}],
            "concern_signal_count": 1,
            "files_to_read": ["b.py", "c.py"],
            "historical_issue_focus": {
                "dimensions": ["error_consistency"],
                "max_items": 5,
                "selected_count": 1,
                "issues": [{"dimension": "error_consistency", "identifier": "i2"}],
            },
        },
    ]
    out = select_batches_for_run(batches, mode="grouped")
    assert len(out) == 1
    merged = out[0]
    assert merged["dimension_prompts"] == {
        "convention_outlier": {"description": "d1"},
        "error_consistency": {"description": "d2"},
    }
    assert merged["judgment_finding_counts"] == {"dup": 6}
    assert merged["mechanical_finding_counts"] == {"large_file": 3}
    assert merged["concern_signal_count"] == 1
    assert merged["concern_signals"][0]["fingerprint"] == "f"
    assert merged["files_to_read"] == ["a.py", "b.py", "c.py"]
    focus = merged["historical_issue_focus"]
    assert focus["selected_count"] == 2
    assert focus["max_items"] == 10
    assert focus["dimensions"] == ["convention_outlier", "error_consistency"]


def test_grouped_prompt_renders_all_dimension_rubrics(tmp_path: Path):
    batches = _dim_batches(["convention_outlier", "error_consistency"])
    merged = select_batches_for_run(batches, mode="grouped")[0]
    merged["dimension_prompts"] = {
        "convention_outlier": {"description": "conv rubric"},
        "error_consistency": {"description": "err rubric"},
    }
    prompt = render_batch_prompt(
        repo_root=tmp_path,
        packet_path=tmp_path / "packet.json",
        batch_index=0,
        batch=merged,
    )
    assert "DIMENSIONS TO EVALUATE" in prompt
    assert "conv rubric" in prompt
    assert "err rubric" in prompt
    assert "each of this batch's dimensions" in prompt


def test_single_dimension_prompt_keeps_singular_wording(tmp_path: Path):
    batch = {
        "name": "naming_quality",
        "dimensions": ["naming_quality"],
        "dimension_prompts": {"naming_quality": {"description": "rubric"}},
    }
    prompt = render_batch_prompt(
        repo_root=tmp_path,
        packet_path=tmp_path / "packet.json",
        batch_index=0,
        batch=batch,
    )
    assert "DIMENSION TO EVALUATE" in prompt
    assert "this batch's dimension" in prompt


def test_run_summary_records_batch_mode(tmp_path: Path):
    written: dict[Path, str] = {}
    config = BatchRunSummaryConfig(
        created_at="2026-11-01T00:00:00+00:00",
        run_stamp="stamp",
        runner="codex",
        run_parallel=False,
        selected_indexes=[0],
        allow_partial=False,
        max_parallel_batches=3,
        batch_timeout_seconds=1200,
        batch_max_retries=1,
        batch_retry_backoff_seconds=2.0,
        heartbeat_seconds=15.0,
        stall_warning_seconds=0,
        stall_kill_seconds=120,
        immutable_packet_path=tmp_path / "packet.json",
        prompt_packet_path=tmp_path / "blind.json",
        run_dir=tmp_path,
        logs_dir=tmp_path / "logs",
        run_log_path=tmp_path / "run.log",
        batch_mode="grouped",
    )
    write_run_summary(
        summary_path=tmp_path / "run_summary.json",
        summary_config=config,
        batch_status={},
        successful_batches=[1],
        failed_batches=[],
        safe_write_text_fn=lambda p, t: written.setdefault(p, t),
        colorize_fn=lambda t, _c: t,
        append_run_log_fn=lambda _m: None,
    )
    import json

    payload = json.loads(written[tmp_path / "run_summary.json"])
    assert payload["batch_mode"] == "grouped"

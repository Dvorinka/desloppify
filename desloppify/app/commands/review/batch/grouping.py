"""Batch granularity selection for review run-batches execution.

Cost control: ``per-dimension`` (default) runs one subagent per dimension
(~20 runs). ``grouped`` merges dimensions that share a holistic evidence
collector into one batch (~9 runs). ``single`` merges everything into one
batch (1 run, cheapest, shallowest).
"""

from __future__ import annotations

from desloppify.intelligence.review.prepare_batches_collectors import (
    _DIMENSION_FILE_MAPPING,
)

from ..prompt_sections import (
    PromptBatchPayload,
    explode_to_single_dimension,
)

BATCH_MODES = ("per-dimension", "grouped", "single")
DEFAULT_BATCH_MODE = "per-dimension"
_SINGLE_BATCH_NAME = "all_dimensions"


def resolve_batch_mode(raw: object) -> str:
    """Normalize a user/summary-supplied batch mode string."""
    mode = str(raw or "").strip().lower()
    return mode if mode in BATCH_MODES else DEFAULT_BATCH_MODE


def batch_mode_for_args(args: object) -> str:
    """Resolve the effective batch mode from parsed CLI args."""
    return resolve_batch_mode(getattr(args, "batch_mode", None))


def _merge_finding_counts(
    members: list[PromptBatchPayload],
    key: str,
) -> dict[str, float]:
    merged: dict[str, float] = {}
    for member in members:
        counts = member.get(key)
        if not isinstance(counts, dict):
            continue
        for detector, count in counts.items():
            if isinstance(count, bool) or not isinstance(count, int | float):
                continue
            merged[str(detector)] = merged.get(str(detector), 0) + count
    return merged


def _merge_issue_focus(members: list[PromptBatchPayload], dims: list[str]) -> dict | None:
    focuses = [
        member["historical_issue_focus"]
        for member in members
        if isinstance(member.get("historical_issue_focus"), dict)
    ]
    if not focuses:
        return None
    issues: list[object] = []
    max_items = 0
    for focus in focuses:
        raw_max = focus.get("max_items", 0)
        if isinstance(raw_max, int | float) and not isinstance(raw_max, bool):
            max_items += int(raw_max)
        for issue in focus.get("issues", []):
            issues.append(issue)
    return {
        "dimensions": list(dims),
        "max_items": max_items or len(issues),
        "selected_count": len(issues),
        "issues": issues,
    }


def _merge_member_dicts(members: list[PromptBatchPayload], key: str) -> dict:
    merged: dict = {}
    for member in members:
        value = member.get(key)
        if isinstance(value, dict):
            merged.update(value)
    return merged


def _merge_member_list(members: list[PromptBatchPayload], key: str) -> list[str]:
    out: list[str] = []
    for member in members:
        value = member.get(key)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, str) and item and item not in out:
                out.append(item)
    return out


def merge_batch_members(
    members: list[PromptBatchPayload],
    *,
    name: str,
    why: str,
) -> PromptBatchPayload:
    """Merge per-dimension batch payloads into one multi-dimension batch."""
    dims: list[str] = []
    for member in members:
        for dim in member.get("dimensions", []):
            if isinstance(dim, str) and dim and dim not in dims:
                dims.append(dim)

    merged: PromptBatchPayload = {**members[0]}
    merged["name"] = name
    merged["dimensions"] = dims
    merged["why"] = why

    dimension_prompts = _merge_member_dicts(members, "dimension_prompts")
    if dimension_prompts:
        merged["dimension_prompts"] = dimension_prompts
    else:
        merged.pop("dimension_prompts", None)

    concern_signals = [
        signal
        for member in members
        for signal in member.get("concern_signals", [])
        if isinstance(signal, dict)
    ]
    if concern_signals:
        merged["concern_signals"] = concern_signals
        merged["concern_signal_count"] = len(concern_signals)
    else:
        merged.pop("concern_signals", None)
        merged.pop("concern_signal_count", None)

    for key in ("judgment_finding_counts", "mechanical_finding_counts"):
        counts = _merge_finding_counts(members, key)
        if counts:
            merged[key] = counts  # type: ignore[literal-required]
        else:
            merged.pop(key, None)

    issue_focus = _merge_issue_focus(members, dims)
    if issue_focus is not None:
        merged["historical_issue_focus"] = issue_focus
    else:
        merged.pop("historical_issue_focus", None)

    defer_meta = _merge_member_dicts(members, "subjective_defer_meta")
    if defer_meta:
        merged["subjective_defer_meta"] = defer_meta
    else:
        merged.pop("subjective_defer_meta", None)

    files = _merge_member_list(members, "files_to_read")
    if files:
        merged["files_to_read"] = files
    else:
        merged.pop("files_to_read", None)

    dimension_contexts = _merge_member_dicts(members, "dimension_contexts")
    if dimension_contexts:
        merged["dimension_contexts"] = dimension_contexts  # type: ignore[literal-required]
    else:
        merged.pop("dimension_contexts", None)

    return merged


def select_batches_for_run(
    batches: list[dict],
    *,
    mode: str,
    dimension_prompts: dict[str, dict[str, object]] | None = None,
) -> list[PromptBatchPayload]:
    """Explode then regroup investigation batches per the requested mode."""
    exploded = explode_to_single_dimension(
        [b for b in batches if isinstance(b, dict)],
        dimension_prompts=dimension_prompts,
    )
    resolved = resolve_batch_mode(mode)
    if resolved == "per-dimension" or not exploded:
        return exploded

    if resolved == "single":
        return [
            merge_batch_members(
                exploded,
                name=_SINGLE_BATCH_NAME,
                why="single-agent review covering all selected dimensions",
            )
        ]

    groups: dict[str, list[PromptBatchPayload]] = {}
    order: list[str] = []
    for batch in exploded:
        dims = batch.get("dimensions", [])
        dim = dims[0] if dims else ""
        key = _DIMENSION_FILE_MAPPING.get(dim) or dim or "uncategorized"
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(batch)

    return [
        merge_batch_members(
            groups[key],
            name=key,
            why=f"combined {key} review covering {', '.join(_group_dims(groups[key]))}",
        )
        for key in order
    ]


def _group_dims(members: list[PromptBatchPayload]) -> list[str]:
    dims: list[str] = []
    for member in members:
        for dim in member.get("dimensions", []):
            if isinstance(dim, str) and dim and dim not in dims:
                dims.append(dim)
    return dims


__all__ = [
    "BATCH_MODES",
    "DEFAULT_BATCH_MODE",
    "batch_mode_for_args",
    "merge_batch_members",
    "resolve_batch_mode",
    "select_batches_for_run",
]

"""Auto-complete action steps when their referenced issues leave the queue."""

from __future__ import annotations


def _open_issue_ids(issues: dict | None) -> set[str]:
    """Return IDs of findings that are still open in scan state."""
    if not isinstance(issues, dict):
        return set()
    return {
        issue_id
        for issue_id, issue in issues.items()
        if isinstance(issue_id, str)
        and isinstance(issue, dict)
        and issue.get("status") in {"open", "reopened"}
    }


def auto_complete_steps(plan: dict, *, issues: dict | None = None) -> list[str]:
    """Mark steps done when all their issue_refs leave the living plan.

    Returns list of human-readable messages for completed steps.

    When *issues* (the state work-item map) is provided, a ref is only
    considered resolved when it is absent from the plan AND no open finding
    still matches it — absence from ``queue_order`` alone is not resolution,
    since the execution queue is a subset of the backlog.
    """
    messages: list[str] = []
    actionable_ids = set(plan.get("queue_order", []))
    actionable_ids.update((plan.get("skipped") or {}).keys())
    actionable_ids.update(plan.get("promoted_ids") or [])
    for cluster in (plan.get("clusters") or {}).values():
        if isinstance(cluster, dict):
            actionable_ids.update(cluster.get("issue_ids") or [])
    open_ids = _open_issue_ids(issues)

    def _ref_alive(ref: str) -> bool:
        # Match by suffix: ref "abc123" matches "review::path::abc123"
        return any(
            issue_id.endswith(ref) or issue_id == ref
            for issue_id in (*actionable_ids, *open_ids)
        )

    for name, cluster in plan.get("clusters", {}).items():
        cluster_issue_ids = set(cluster.get("issue_ids") or [])
        for i, step in enumerate(cluster.get("action_steps") or []):
            if not isinstance(step, dict) or step.get("done"):
                continue
            refs = step.get("issue_refs", [])
            if not refs:
                continue
            all_gone = all(not _ref_alive(ref) for ref in refs)
            # Some triage runners emit summary hashes as step refs while the
            # living plan stores canonical issue IDs.  If the cluster still
            # has members, an unmatched ref is ambiguous rather than proof
            # that the step's finding was resolved.  Fail closed and leave
            # the step open until its cluster membership is drained.
            if all_gone and cluster_issue_ids:
                continue
            if all_gone:
                step["done"] = True
                messages.append(
                    f"  Step {i + 1} of '{name}' auto-completed: {step.get('title', '')}"
                )
    return messages


__all__ = ["auto_complete_steps"]

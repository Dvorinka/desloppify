"""Resolve command handler for plan overrides."""

from __future__ import annotations

import argparse
import fnmatch
import logging

from desloppify.app.commands.helpers.attestation import (
    show_attestation_requirement,
    show_note_length_requirement,
    validate_attestation,
    validate_note_length,
)
from desloppify.app.commands.helpers.command_runtime import command_runtime
from desloppify.app.commands.resolve.cmd import cmd_resolve
from desloppify.base.exception_sets import PLAN_LOAD_EXCEPTIONS
from desloppify.base.output.fallbacks import log_best_effort_failure
from desloppify.base.output.terminal import colorize
from desloppify.engine._work_queue.core import ATTEST_EXAMPLE
from desloppify.engine._plan.constants import STRATEGY_PREFIX
from desloppify.engine._plan.operations.lifecycle import purge_ids
from desloppify.engine.plan_state import (
    load_plan,
    save_plan,
)
from desloppify.engine.plan_ops import append_log_entry

from .resolve_helpers import (
    check_cluster_guard,
    split_synthetic_patterns,
)
from .resolve_workflow import resolve_workflow_patterns

logger = logging.getLogger(__name__)


def cmd_plan_resolve(args: argparse.Namespace) -> None:
    """Mark issues as fixed and delegate to resolve command UX."""
    patterns: list[str] = getattr(args, "patterns", [])
    attestation: str | None = getattr(args, "attest", None)
    note: str | None = getattr(args, "note", None)

    if getattr(args, "confirm", False):
        if not note:
            print(colorize("  --confirm requires --note to describe what you did.", "red"))
            return
        attestation = f"I have actually {note} and I am not gaming the score."
        args.attest = attestation

    synthetic_ids, real_patterns = split_synthetic_patterns(patterns)
    if synthetic_ids:
        workflow_outcome = resolve_workflow_patterns(
            args,
            synthetic_ids=synthetic_ids,
            real_patterns=real_patterns,
            note=note,
        )
        if workflow_outcome.status == "blocked":
            return
        if workflow_outcome.status == "handled":
            return
        patterns = workflow_outcome.remaining_patterns
        args.patterns = patterns

    if not validate_note_length(note):
        show_note_length_requirement(note)
        return

    if not validate_attestation(attestation):
        show_attestation_requirement("Plan resolve", attestation, ATTEST_EXAMPLE)
        return

    plan: dict | None = None
    try:
        runtime = command_runtime(args)
        state = runtime.state
        plan = load_plan()
        if check_cluster_guard(patterns, plan, state):
            return
    except PLAN_LOAD_EXCEPTIONS:
        plan = None

    resolve_args = argparse.Namespace(
        status="fixed",
        patterns=patterns,
        note=note,
        attest=attestation,
        confirm_batch_wontfix=False,
        force_resolve=bool(getattr(args, "force_resolve", False)),
        state=getattr(args, "state", None),
        lang=getattr(args, "lang", None),
        path=getattr(args, "path", None),
        exclude=getattr(args, "exclude", None),
    )

    # A guard rejection raises CommandError — the done log entry must not
    # be written for a resolution that did not land (#922).
    cmd_resolve(resolve_args)

    try:
        if plan is None:
            plan = load_plan()
        # Resolved strategy items still carry a synthetic prefix — the real
        # resolve path marks them fixed in state but nothing drops them from
        # queue_order/skipped/clusters without an explicit purge (#879).
        strategy_patterns = [
            pattern for pattern in patterns if pattern.startswith(STRATEGY_PREFIX)
        ]
        if strategy_patterns:
            plan_ids = {
                *plan.get("queue_order", []),
                *plan.get("skipped", {}),
                *plan.get("overrides", {}),
                *(
                    issue_id
                    for cluster in plan.get("clusters", {}).values()
                    if isinstance(cluster, dict)
                    for issue_id in cluster.get("issue_ids", [])
                ),
            }
            resolved_strategy = [
                issue_id
                for issue_id in plan_ids
                if isinstance(issue_id, str)
                and issue_id.startswith(STRATEGY_PREFIX)
                and any(
                    fnmatch.fnmatch(issue_id, pattern)
                    for pattern in strategy_patterns
                )
            ]
            if resolved_strategy:
                purge_ids(plan, resolved_strategy)
        clusters = plan.get("clusters", {})
        cluster_name = next((pattern for pattern in patterns if pattern in clusters), None)
        append_log_entry(
            plan,
            "done",
            issue_ids=patterns,
            cluster_name=cluster_name,
            actor="user",
            note=note,
        )
        save_plan(plan)
    except PLAN_LOAD_EXCEPTIONS as exc:
        log_best_effort_failure(logger, "append plan resolve log entry", exc)
        print(colorize(f"  Note: unable to append plan resolve log entry ({exc}).", "dim"))


__all__ = ["cmd_plan_resolve"]

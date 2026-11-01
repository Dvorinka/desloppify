"""PR diff review: map scan findings onto base..head changed lines.

Purely mechanical — no LLM. Resolves the diff hunks for ``base...HEAD``,
filters open findings to changed lines, and reports annotations plus the
strict-score delta. Used by ``scan --diff`` and the bundled GitHub Action.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from desloppify.base.exception_sets import CommandError
from desloppify.base.output.terminal import colorize
from desloppify.base.discovery.file_paths import rel

_HUNK_RE = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def changed_line_ranges(base: str, *, cwd: Path) -> dict[str, list[tuple[int, int]]]:
    """Return {repo-relative path: [(start, end)]} for base...HEAD."""
    try:
        proc = subprocess.run(
            ["git", "diff", "--unified=0", "--find-renames", f"{base}...HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise CommandError(f"git diff failed to start: {exc}") from exc
    if proc.returncode != 0:
        raise CommandError(
            f"git diff {base}...HEAD failed: {proc.stderr.strip() or proc.stdout.strip()}"
        )

    ranges: dict[str, list[tuple[int, int]]] = {}
    current_file: str | None = None
    for raw in proc.stdout.splitlines():
        if raw.startswith("+++ b/"):
            current_file = raw[6:]
            continue
        if raw.startswith("+++ /dev/null"):
            current_file = None
            continue
        match = _HUNK_RE.match(raw)
        if match and current_file:
            start = int(match.group(1))
            count = int(match.group(2) or 1)
            ranges.setdefault(current_file, []).append(
                (start, start + max(count, 1) - 1)
            )
    return ranges


def _issue_line(issue: dict[str, Any]) -> int | None:
    detail = issue.get("detail")
    if isinstance(detail, dict):
        for key in ("line", "start_line"):
            value = detail.get(key)
            if isinstance(value, int | float) and not isinstance(value, bool):
                return int(value)
    value = issue.get("line")
    if isinstance(value, int | float) and not isinstance(value, bool):
        return int(value)
    return None


def annotations_for_issues(
    issues: dict[str, Any] | list[dict[str, Any]],
    ranges: dict[str, list[tuple[int, int]]],
) -> list[dict[str, Any]]:
    """Filter open findings to those intersecting the diff's changed lines.

    Findings without line info on a changed file are included as file-level
    annotations — better noisy than silently dropped.
    """
    items = issues.values() if isinstance(issues, dict) else issues
    annotations: list[dict[str, Any]] = []
    for issue in items:
        if not isinstance(issue, dict) or issue.get("status") != "open":
            continue
        issue_file = rel(str(issue.get("file") or ""))
        file_ranges = ranges.get(issue_file)
        if file_ranges is None:
            continue
        line = _issue_line(issue)
        if line is not None and not any(
            start <= line <= end for start, end in file_ranges
        ):
            continue
        detail = issue.get("detail") if isinstance(issue.get("detail"), dict) else {}
        annotations.append(
            {
                "id": issue.get("id"),
                "file": issue_file,
                "line": line,
                "detector": issue.get("detector"),
                "check": detail.get("kind"),
                "tier": issue.get("tier"),
                "confidence": issue.get("confidence"),
                "severity": detail.get("severity"),
                "summary": issue.get("summary"),
            }
        )
    annotations.sort(
        key=lambda a: (a["file"], a["line"] if a["line"] is not None else 0)
    )
    return annotations


def print_diff_report(
    annotations: list[dict[str, Any]],
    *,
    prev_strict: float | None,
    new_strict: float | None,
    base: str,
) -> None:
    """Print the diff-review section and GHA workflow-command annotations."""
    print(colorize(f"\n  Diff review ({base}...HEAD)", "bold"))
    if not annotations:
        print(colorize("  No findings on changed lines.", "green"))
    for ann in annotations:
        location = f"{ann['file']}:{ann['line']}" if ann["line"] else ann["file"]
        label = ann["check"] or ann["detector"] or "finding"
        print(f"  {location}: [{label}] {ann['summary']}")

    if os.environ.get("GITHUB_ACTIONS"):
        for ann in annotations:
            location = f"file={ann['file']}"
            if ann["line"]:
                location += f",line={ann['line']}"
            title = (ann["check"] or ann["detector"] or "finding").replace(
                "\n", " "
            )
            summary = str(ann["summary"] or "").replace("\n", " ")
            print(f"::warning {location},title={title}::{summary}")

    if prev_strict is not None and new_strict is not None:
        delta = new_strict - prev_strict
        sign = "+" if delta >= 0 else ""
        print(
            colorize(
                f"  Strict score: {prev_strict:.1f} -> {new_strict:.1f} "
                f"({sign}{delta:.1f})",
                "cyan" if delta >= 0 else "red",
            )
        )


def write_annotations_json(
    path: str | Path,
    annotations: list[dict[str, Any]],
    *,
    base: str,
    prev_strict: float | None,
    new_strict: float | None,
) -> None:
    """Emit machine-readable annotations for CI consumers."""
    payload = {
        "base": base,
        "strict_before": prev_strict,
        "strict_after": new_strict,
        "strict_delta": (
            round(new_strict - prev_strict, 2)
            if prev_strict is not None and new_strict is not None
            else None
        ),
        "annotations": annotations,
    }
    Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


__all__ = [
    "annotations_for_issues",
    "changed_line_ranges",
    "print_diff_report",
    "write_annotations_json",
]

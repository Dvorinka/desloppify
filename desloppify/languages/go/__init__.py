"""Go language configuration for Desloppify.

Originally contributed by tinker495 (KyuSeok Jung) in PR #128.
Upgraded from generic_lang to full class-based plugin.
"""

from __future__ import annotations

import re
import subprocess  # nosec B404
from functools import lru_cache
from pathlib import Path
from typing import Any

from desloppify.base.discovery.paths import get_area
from desloppify.languages._framework.base.phase_builders import (
    detector_phase_security,
    detector_phase_signature,
    detector_phase_test_coverage,
    shared_subjective_duplicates_tail,
)
from desloppify.languages._framework.base.types import DetectorPhase, LangConfig
from desloppify.languages._framework.generic_support.core import make_tool_phase
from desloppify.languages._framework.registry.registration import register_full_plugin
from desloppify.languages._framework.registry.state import register_lang_hooks
from desloppify.languages._framework.treesitter.phases import all_treesitter_phases
from desloppify.languages.go import test_coverage as go_test_coverage_hooks
from desloppify.languages.go.commands import get_detect_commands
from desloppify.languages.go.detectors.deps import build_dep_graph as build_go_dep_graph
from desloppify.languages.go.extractors import (
    GO_FILE_EXCLUSIONS,
    extract_functions,
    find_go_files,
)
from desloppify.languages.go.phases import phase_structural
from desloppify.languages.go.review import (
    HOLISTIC_REVIEW_DIMENSIONS,
    LOW_VALUE_PATTERN,
    MIGRATION_MIXED_EXTENSIONS,
    MIGRATION_PATTERN_PAIRS,
    REVIEW_GUIDANCE,
    api_surface,
    module_patterns,
)

from desloppify.languages.go._zones import GO_ZONE_RULES

GO_ENTRY_PATTERNS = ["/main.go", "/cmd/"]

_GOLANGCI_CMD_V1 = "golangci-lint run --out-format=json"
_GOLANGCI_CMD_V2 = "golangci-lint run --output.json.path stdout"


@lru_cache(maxsize=1)
def _golangci_major() -> int | None:
    """Return the installed golangci-lint major version, or None if unknown."""
    try:
        proc = subprocess.run(
            ["golangci-lint", "version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"version\s+v?(\d+)\.", proc.stdout or "")
    return int(match.group(1)) if match else None


def _golangci_cmd(_path: Path, _lang: Any) -> str | None:
    """Pick the golangci-lint JSON-output flag for the installed major.

    v2 removed ``--out-format`` (issue #887); its JSON-to-stdout spelling is
    ``--output.json.path stdout``.  ``None`` keeps the v1 command when the
    version cannot be read — the tool-missing path already handles that.
    """
    if (_golangci_major() or 0) >= 2:
        return _GOLANGCI_CMD_V2
    return None

class GoConfig(LangConfig):
    """Go language configuration."""

    def __init__(self):
        super().__init__(
            name="go",
            extensions=[".go"],
            exclusions=GO_FILE_EXCLUSIONS,
            default_src=".",
            build_dep_graph=build_go_dep_graph,
            entry_patterns=GO_ENTRY_PATTERNS,
            barrel_names=set(),
            phases=[
                DetectorPhase("Structural analysis", phase_structural),
                make_tool_phase(
                    "golangci-lint",
                    _GOLANGCI_CMD_V1,
                    "golangci",
                    "golangci_lint",
                    tier=2,
                    cmd_fn=_golangci_cmd,
                ),
                make_tool_phase(
                    "go vet", "go vet ./...", "gnu", "vet_error", tier=3
                ),
                *all_treesitter_phases("go"),
                detector_phase_signature(),
                detector_phase_test_coverage(),
                detector_phase_security(),
                *shared_subjective_duplicates_tail(),
            ],
            fixers={},
            get_area=get_area,
            detect_commands=get_detect_commands(),
            boundaries=[],
            typecheck_cmd="go vet ./...",
            file_finder=find_go_files,
            large_threshold=500,
            complexity_threshold=15,
            default_scan_profile="full",
            detect_markers=["go.mod"],
            external_test_dirs=[],
            test_file_extensions=[".go"],
            review_module_patterns_fn=module_patterns,
            review_api_surface_fn=api_surface,
            review_guidance=REVIEW_GUIDANCE,
            review_low_value_pattern=LOW_VALUE_PATTERN,
            holistic_review_dimensions=HOLISTIC_REVIEW_DIMENSIONS,
            migration_pattern_pairs=MIGRATION_PATTERN_PAIRS,
            migration_mixed_extensions=MIGRATION_MIXED_EXTENSIONS,
            extract_functions=extract_functions,
            zone_rules=GO_ZONE_RULES,
        )


def register() -> None:
    """Register Go language config + hooks through an explicit entrypoint."""
    register_full_plugin(
        "go",
        GoConfig,
        test_coverage=go_test_coverage_hooks,
    )


def register_hooks() -> None:
    """Register Go hook modules without language-config bootstrap."""
    register_lang_hooks("go", test_coverage=go_test_coverage_hooks)

Config = GoConfig


__all__ = [
    "Config",
    "GoConfig",
    "register",
    "register_hooks",
    "GO_ENTRY_PATTERNS",
    "GO_ZONE_RULES",
    "HOLISTIC_REVIEW_DIMENSIONS",
    "LOW_VALUE_PATTERN",
    "MIGRATION_MIXED_EXTENSIONS",
    "MIGRATION_PATTERN_PAIRS",
    "REVIEW_GUIDANCE",
]

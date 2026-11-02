"""Swift language plugin — swiftlint."""

from desloppify.engine.policy.zones import Zone, ZoneRule
from desloppify.languages._framework.generic_support.core import (
    generic_lang,
    generic_zone_rules,
)
from desloppify.languages._framework.treesitter import SWIFT_SPEC

SWIFT_ZONE_RULES = [
    # SwiftPM test targets conventionally live in Tests/<Target>Tests/ —
    # the case-sensitive common /tests/ rule misses them (#942).
    ZoneRule(Zone.TEST, ["/Tests/"]),
] + generic_zone_rules([".swift"])

generic_lang(
    name="swift",
    extensions=[".swift"],
    tools=[
        {
            "label": "swiftlint",
            "cmd": "swiftlint lint --reporter json",
            "fmt": "json",
            "id": "swiftlint_violation",
            "tier": 2,
            "fix_cmd": "swiftlint --fix",
        },
    ],
    depth="shallow",
    detect_markers=["Package.swift"],
    treesitter_spec=SWIFT_SPEC,
    zone_rules=SWIFT_ZONE_RULES,
)

__all__ = [
    "generic_lang",
    "SWIFT_ZONE_RULES",
    "SWIFT_SPEC",
]

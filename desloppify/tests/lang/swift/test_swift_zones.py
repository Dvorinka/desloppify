"""Zone classification regression for #942: SwiftPM Tests/ is a test zone."""

from __future__ import annotations

import pytest

from desloppify.engine.policy.zones import Zone, classify_file
from desloppify.languages.swift import SWIFT_ZONE_RULES


@pytest.mark.parametrize(
    "path",
    [
        "Tests/ExampleTests/ExampleTests.swift",
        "Tests/ExampleTests/Fixtures.swift",
        "Packages/Foo/Tests/FooTests/FooTests.swift",
        "tests/lower/lower.swift",
    ],
)
def test_swiftpm_tests_dirs_are_test_zone(path: str) -> None:
    assert classify_file(path, SWIFT_ZONE_RULES) is Zone.TEST


@pytest.mark.parametrize(
    "path",
    [
        "Sources/App/main.swift",
        "Contests/main.swift",
        "Tests.swift",
        "MyTests/helper.swift",
    ],
)
def test_non_test_paths_stay_production(path: str) -> None:
    assert classify_file(path, SWIFT_ZONE_RULES) is Zone.PRODUCTION

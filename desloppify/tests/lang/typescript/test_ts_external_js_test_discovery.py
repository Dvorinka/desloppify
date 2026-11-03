"""Production-phase regression for #944: TS scans must discover JS tests.

TypeScript production discovery only yields .ts/.tsx files, so JavaScript
test files (.js/.jsx/.mjs/.cjs) must reach the coverage phase through
``_find_external_test_files`` — both when the test directory sits inside the
scan root (root scan) and outside it (subdirectory scan). Unrelated
production modules must remain flagged as untested.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from desloppify.engine.policy.zones import FileZoneMap
from desloppify.languages._framework.base.shared_phases_review import (
    phase_test_coverage,
)
from desloppify.languages.typescript import TypeScriptConfig
from desloppify.languages.typescript._zones import TS_ZONE_RULES

_PRODUCTION_BODY = "\n".join(
    [
        "export function compute(input: number): number {",
        "  let total = input;",
        "  for (let i = 0; i < 3; i++) {",
        "    total += i * 2;",
        "  }",
        "  if (total > 10) {",
        "    return total - 1;",
        "  }",
        "  return total;",
        "}",
        "",
        "export const marker = compute(1);",
    ]
)


def _make_lang(files: list[str]) -> TypeScriptConfig:
    lang = TypeScriptConfig()
    lang.zone_map = FileZoneMap(files, TS_ZONE_RULES)
    lang.dep_graph = {
        name: {"imports": set(), "importer_count": 0} for name in files
    }
    lang.complexity_map = {}
    return lang


def _issue_files(issues: list[dict]) -> set[str]:
    return {issue["file"] for issue in issues}


@pytest.mark.parametrize("test_ext", [".js", ".jsx", ".mjs", ".cjs"])
@pytest.mark.parametrize("scan_subdir", [False, True])
def test_ts_scan_discovers_javascript_tests(
    set_project_root: Path, monkeypatch, test_ext: str, scan_subdir: bool
) -> None:
    root = set_project_root
    monkeypatch.chdir(root)
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "src" / "value.ts").write_text(_PRODUCTION_BODY)
    (root / "src" / "unrelated.ts").write_text(_PRODUCTION_BODY)
    (root / "tests" / f"value.test{test_ext}").write_text(
        "import { compute } from '../src/value';\n"
        "test('compute works', () => { expect(compute(1)).toBe(1); });\n"
    )

    files = ["src/value.ts", "src/unrelated.ts"]
    lang = _make_lang(files)
    scan_path = root / "src" if scan_subdir else root

    issues, potentials = phase_test_coverage(scan_path, lang)

    flagged = _issue_files(issues)
    assert "src/value.ts" not in flagged
    assert "src/unrelated.ts" in flagged
    assert potentials["test_coverage"] > 0


def test_ts_scan_without_javascript_tests_still_flags_all(
    set_project_root: Path, monkeypatch
) -> None:
    root = set_project_root
    monkeypatch.chdir(root)
    (root / "src").mkdir()
    (root / "src" / "value.ts").write_text(_PRODUCTION_BODY)
    (root / "src" / "unrelated.ts").write_text(_PRODUCTION_BODY)

    files = ["src/value.ts", "src/unrelated.ts"]
    issues, _ = phase_test_coverage(root, _make_lang(files))

    assert _issue_files(issues) == set(files)

"""C# branches in test coverage mapping should be safe and usable."""

import pytest

from desloppify.engine.detectors.coverage.mapping import (
    _map_test_to_source,
    analyze_test_quality,
    import_based_mapping,
)
from desloppify.languages.csharp.detectors.deps import build_dep_graph
from desloppify.languages.csharp.test_coverage import parse_test_import_specs


def test_map_test_to_source_csharp_name_convention():
    prod = {"src/UserService.cs"}
    test = "src/Tests/UserServiceTests.cs"
    assert _map_test_to_source(test, prod, "csharp") == "src/UserService.cs"


def test_analyze_test_quality_csharp_assertions(tmp_path):
    test_file = tmp_path / "AuthTests.cs"
    test_file.write_text(
        """
using Xunit;
public class AuthTests
{
    [Fact]
    public void Works()
    {
        Assert.True(true);
    }
}
"""
    )
    result = analyze_test_quality({str(test_file)}, "csharp")
    quality = result[str(test_file)]["quality"]
    assert quality in {"adequate", "thorough", "smoke"}


@pytest.mark.parametrize("unused_name", ["Unused", "Services"])
def test_namespace_import_does_not_mark_unused_sibling_directly_tested(tmp_path, unused_name):
    test = tmp_path / "BehaviorTests.cs"
    exercised = tmp_path / "Exercised.cs"
    unused = tmp_path / f"{unused_name}.cs"
    test.write_text('''using Demo.Services;
namespace Demo.Tests;
class BehaviorTests { object subject = new Exercised(); }
''')
    exercised.write_text("namespace Demo.Services;\nclass Exercised {}")
    unused.write_text(f"namespace Demo.Services;\nclass {unused_name} {{}}")

    graph = build_dep_graph(tmp_path)
    tested = import_based_mapping(
        graph, {str(test)}, {str(exercised), str(unused)}, "csharp"
    )

    assert tested == {str(exercised)}


def test_source_import_supplement_uses_explicit_types_only():
    content = "\n".join([
        "using Demo.Services;",
        "using Alias = Demo.Services;",
        "using static Demo.Tools.MathHelpers;",
        "global using static Demo.Tools.TextHelpers;",
    ])

    assert parse_test_import_specs(content) == ["Demo.Tools.MathHelpers", "Demo.Tools.TextHelpers"]


def test_static_import_supplement_resolves_declaration_not_filename(tmp_path):
    test = tmp_path / "BehaviorTests.cs"
    implementation = tmp_path / "Implementation.cs"
    misleading = tmp_path / "MathHelpers.cs"
    test.write_text("using static Demo.Tools.MathHelpers;\nclass BehaviorTests {}")
    implementation.write_text("namespace Demo.Tools;\nstatic class MathHelpers {}")
    misleading.write_text("namespace Demo.Other;\nclass Other {}")

    tested = import_based_mapping(
        {}, {str(test)}, {str(implementation), str(misleading)}, "csharp"
    )

    assert tested == {str(implementation)}


def test_external_static_import_does_not_match_local_filename(tmp_path):
    test = tmp_path / "BehaviorTests.cs"
    local = tmp_path / "Math.cs"
    test.write_text("using static System.Math;\nclass BehaviorTests {}")
    local.write_text("namespace Demo.Tools;\nclass Math {}")

    assert import_based_mapping({}, {str(test)}, {str(local)}, "csharp") == set()


def test_analyze_test_quality_custom_harness_is_unknown_not_no_tests(tmp_path):
    """#892: a scenario file calling a custom Check.That helper must not be
    reported as confidently having no tests."""
    test_file = tmp_path / "CounterScenarios.cs"
    test_file.write_text(
        "namespace Sample.Tests;\n"
        "public static class CounterScenarios {\n"
        "    public static void AddsPositiveAmounts() {\n"
        "        var counter = new Counter();\n"
        "        counter.Add(2);\n"
        '        Check.That(counter.Value == 2, "amount is retained");\n'
        "        counter.Add(3);\n"
        '        Check.That(counter.Value == 5, "amounts accumulate");\n'
        "    }\n"
        "}\n"
    )
    result = analyze_test_quality({str(test_file)}, "csharp")
    assert result[str(test_file)]["assertions"] == 2
    assert result[str(test_file)]["test_functions"] == 0
    assert result[str(test_file)]["quality"] == "unknown"


def test_analyze_test_quality_truly_empty_file_stays_no_tests(tmp_path):
    test_file = tmp_path / "Empty.cs"
    test_file.write_text("namespace Sample.Tests;\npublic static class Empty {}\n")
    result = analyze_test_quality({str(test_file)}, "csharp")
    assert result[str(test_file)]["quality"] == "no_tests"

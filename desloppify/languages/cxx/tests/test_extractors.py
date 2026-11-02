from __future__ import annotations

import time
from pathlib import Path

import desloppify.languages.cxx.extractors as cxx_extractors
from desloppify.languages.cxx.extractors import (
    extract_all_cxx_functions,
    find_cxx_files,
)


def test_extract_cxx_functions_and_classes(tmp_path):
    source = tmp_path / "widget.cpp"
    source.write_text("class Widget { void run(); }; void helper() {}\n")

    functions = extract_all_cxx_functions([str(source)])

    assert any(f.name == "helper" for f in functions)


def test_extract_cxx_function_ignores_comment_braces(tmp_path):
    source = tmp_path / "widget.cpp"
    source.write_text(
        """
int helper() {
    /* unbalanced } }} braces */
    return 1;
}
"""
    )

    functions = extract_all_cxx_functions([str(source)])

    assert [fn.name for fn in functions] == ["helper"]
    assert "return 1;" in functions[0].body


def test_extract_all_cxx_functions_treats_string_root_as_path(tmp_path):
    source = tmp_path / "widget.cpp"
    source.write_text("int widget() { return 1; }\n")

    functions = extract_all_cxx_functions(str(tmp_path))

    assert [fn.name for fn in functions] == ["widget"]


def test_find_cxx_files_includes_common_header_only_extensions(tmp_path):
    files = [
        tmp_path / "widget.hh",
        tmp_path / "widget.hxx",
        tmp_path / "widget.ipp",
        tmp_path / "widget.inl",
        tmp_path / "widget.tpp",
        tmp_path / "widget.txx",
        tmp_path / "widget.tcc",
    ]
    for path in files:
        path.write_text("// test\n")

    discovered = {str(Path(filepath).resolve()) for filepath in find_cxx_files(tmp_path)}

    assert discovered == {str(path.resolve()) for path in files}


def test_cxx_extractors_use_local_brace_helper():
    assert cxx_extractors.find_matching_brace.__module__ == "desloppify.languages.cxx._parse_helpers"


def test_extract_keywords_never_become_function_names(tmp_path):
    """#903: `else if (cond) {` must not extract a function named `if`."""
    source = tmp_path / "control.cpp"
    source.write_text(
        """
int classify(int x) {
    if (x > 0) {
        return 1;
    } else if (x < 0) {
        return -1;
    }
    return 0;
}
"""
    )
    functions = extract_all_cxx_functions([str(source)])
    assert [f.name for f in functions] == ["classify"]


def test_extract_member_defs_keep_owner_qualifier(tmp_path):
    """#903: A::EndPlay and B::EndPlay are distinct member contracts."""
    a = tmp_path / "a.cpp"
    b = tmp_path / "b.cpp"
    a.write_text("void A::EndPlay(Reason Reason) { done(); }\n")
    b.write_text("void B::EndPlay(const Reason Reason) { done(); }\n")

    functions = extract_all_cxx_functions([str(a), str(b)])
    names = sorted(f.name for f in functions)
    assert names == ["A::EndPlay", "B::EndPlay"]
    # top-level const on a by-value param does not change the signature
    assert functions[0].params == functions[1].params == ["Reason"]


def test_extract_params_normalizes_names_and_qualifiers(tmp_path):
    source = tmp_path / "params.cpp"
    source.write_text(
        "void f(int count, const char* name, Reason& reason, EMode mode = EMode::Fast) {}\n"
    )
    functions = extract_all_cxx_functions([str(source)])
    assert functions[0].params == ["int", "char", "Reason", "EMode"]


def test_func_decl_bounds_qualified_name_backtracking(tmp_path):
    source = tmp_path / "deep.cpp"
    source.write_text("::".join(["Type"] * 21) + " value = source;\n")

    started = time.perf_counter()
    functions = extract_all_cxx_functions([str(source)])
    elapsed = time.perf_counter() - started

    assert functions == []
    assert elapsed < 0.25

"""Tests for TypeScript move helpers."""

from __future__ import annotations

import desloppify.languages.typescript.move as ts_move


def test_move_ts_module_imports():
    assert callable(ts_move.find_replacements)
    assert callable(ts_move.find_self_replacements)


class TestMoveTsHelpers:
    def test_strip_ts_ext(self):
        assert ts_move._strip_ts_ext("foo.ts") == "foo"
        assert ts_move._strip_ts_ext("foo.tsx") == "foo"
        assert ts_move._strip_ts_ext("foo.js") == "foo"
        assert ts_move._strip_ts_ext("foo.jsx") == "foo"
        assert ts_move._strip_ts_ext("foo") == "foo"
        assert ts_move._strip_ts_ext("foo.css") == "foo.css"

    def test_compute_ts_specifiers_relative(self):
        alias, relative = ts_move._compute_ts_specifiers(
            "/project/src/a.ts", "/project/src/b.ts"
        )
        assert relative == "./b"
        assert alias is None

    def test_compute_ts_specifiers_parent(self):
        alias, relative = ts_move._compute_ts_specifiers(
            "/project/src/sub/a.ts", "/project/src/b.ts"
        )
        assert relative == "../b"
        assert alias is None

    def test_strip_index_from_relative(self):
        alias, relative = ts_move._compute_ts_specifiers(
            "/project/src/a.ts",
            "/project/src/utils/index.ts",
        )
        assert relative == "./utils"
        assert not relative.endswith("/index")
        assert alias is None


class TestFormReplacements:
    def test_explicit_ts_extension_preserved(self):
        content = "import type { V } from './types.ts';\n"
        repl = ts_move._form_replacements(
            content, "./types", "./group/types",
            old_is_index=False, new_is_index=False,
        )
        assert repl == [("'./types.ts'", "'./group/types.ts'")]

    def test_emitted_js_specifier_rewritten(self):
        content = 'import { V } from "./types.js";\n'
        repl = ts_move._form_replacements(
            content, "./types", "./group/types",
            old_is_index=False, new_is_index=False,
        )
        assert repl == [('"./types.js"', '"./group/types.js"')]

    def test_index_spelling_not_matched_as_sibling_file(self):
        # ./utils.ts names a sibling file, not ./utils/index.ts — leave it.
        content = "import { u } from './utils.ts';\n"
        repl = ts_move._form_replacements(
            content, "./utils", "./lib/utils",
            old_is_index=True, new_is_index=True,
        )
        assert repl == []

    def test_index_form_preserved(self):
        content = "import { u } from './utils/index';\n"
        repl = ts_move._form_replacements(
            content, "./utils", "./lib/utils",
            old_is_index=True, new_is_index=True,
        )
        assert repl == [("'./utils/index'", "'./lib/utils/index'")]

    def test_extensionless_still_matched(self):
        content = "import { V } from './types';\n"
        repl = ts_move._form_replacements(
            content, "./types", "./group/types",
            old_is_index=False, new_is_index=False,
        )
        assert repl == [("'./types'", "'./group/types'")]

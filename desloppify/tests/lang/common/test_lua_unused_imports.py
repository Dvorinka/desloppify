"""Regression tests for Lua import detection (#940).

The import query must only treat ``require(...)`` as an import — every
``function_call`` with a string argument used to match, so ``load`` modes,
``string.pack``/``unpack`` format specifiers, assert messages, and table
keys were all flagged as "unused imports".
"""

from __future__ import annotations

import textwrap


def _detect(tmp_path, contents: str):
    from desloppify.languages._framework.treesitter.analysis.unused_imports import (
        detect_unused_imports,
    )
    from desloppify.languages._framework.treesitter.specs.scripting import LUA_SPEC

    script = tmp_path / "mod.lua"
    script.write_text(textwrap.dedent(contents).lstrip())
    return detect_unused_imports([str(script)], LUA_SPEC)


def test_lua_string_literal_calls_are_not_imports(tmp_path):
    findings = _detect(
        tmp_path,
        """
        local src = "return 1"
        local p = "b"
        load(src, "=" .. p, "t")
        string.pack("<f", 1)
        string.unpack(">d", "x")
        assert(true, "cannot load xjvm core")
        local t = { ["UTF-16BE"] = 1 }
        print("]")
        """,
    )

    assert findings == []


def test_lua_require_is_still_an_import(tmp_path):
    findings = _detect(
        tmp_path,
        """
        local m = require("lib.beta")
        local x = 1
        return x
        """,
    )

    assert findings == [{"file": findings[0]["file"], "line": 1, "name": "beta"}]


def test_lua_used_require_is_not_flagged(tmp_path):
    findings = _detect(
        tmp_path,
        """
        local alpha = require("lib.alpha")
        alpha.run()
        return alpha
        """,
    )

    assert findings == []


def test_lua_bare_require_string_form(tmp_path):
    findings = _detect(
        tmp_path,
        """
        local g = require "lib.gamma"
        local y = 2
        return y
        """,
    )

    assert findings == [{"file": findings[0]["file"], "line": 1, "name": "gamma"}]

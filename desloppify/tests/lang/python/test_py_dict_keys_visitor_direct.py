"""Direct tests for DictKeyVisitor internals."""

from __future__ import annotations

import ast

from desloppify.languages.python.detectors.dict_keys.visitor import DictKeyVisitor


def test_dict_key_visitor_captures_dict_literals_for_schema_drift():
    source = """
def build_payload():
    return {"a": 1, "b": 2, "c": 3}
"""
    visitor = DictKeyVisitor("sample.py")
    visitor.visit(ast.parse(source))

    assert len(visitor._dict_literals) == 1
    literal = visitor._dict_literals[0]
    assert literal["file"] == "sample.py"
    assert literal["keys"] == frozenset({"a", "b", "c"})


def test_dict_key_visitor_handles_basic_writes_and_reads_without_crashing():
    source = """
def update():
    state = {}
    state["x"] = 1
    return state.get("x")
"""
    visitor = DictKeyVisitor("sample.py")
    visitor.visit(ast.parse(source))

    assert isinstance(visitor._issues, list)
    assert isinstance(visitor._dict_literals, list)


def _issue_kinds(source: str) -> list[tuple[str, str]]:
    visitor = DictKeyVisitor("sample.py")
    visitor.visit(ast.parse(source))
    return [(item["kind"], item["key"]) for item in visitor._issues]


def test_cross_method_self_dict_consumption_not_dead_write():
    """#801: self.x consumed by another method is not a dead write."""
    issues = _issue_kinds(
        """class Reporter:
    def collect(self):
        self.evidence = {"count": 1, "source": "fixture", "valid": True}
    def publish(self):
        return self.evidence
"""
    )
    assert issues == []


def test_conditional_override_not_overwritten_key():
    """#801: default + conditional override is intentional, not an overwrite."""
    issues = _issue_kinds(
        """def select(enabled):
    record = {"mode": "default", "a": 0, "b": 0}
    if enabled:
        record["mode"] = "selected"
    return record
"""
    )
    assert issues == []


def test_mutated_after_call_escape_not_phantom_read():
    """#801: a dict passed to a call may gain keys — no phantom claim."""
    issues = _issue_kinds(
        """def fill(record):
    record["value"] = 2

def create():
    record = {"id": 1}
    fill(record)
    return record["value"]
"""
    )
    assert issues == []


def test_type_guard_fallback_rebinding_not_phantom():
    """#846: rebound-to-literal after external value has unknown provenance."""
    issues = _issue_kinds(
        """from collections.abc import Mapping

def read_provider_payload(raw: Mapping[str, object]):
    nested = raw.get("nested", {})
    if not isinstance(nested, Mapping):
        nested = {}
    return nested.get("provider_field")
"""
    )
    assert issues == []


def test_whole_dict_sequence_alias_not_dead_write():
    """#846: a dict moved through a for-iter container escapes."""
    issues = _issue_kinds(
        """def consume_scope(*, allowed):
    return bool(allowed)

def normalize_scopes():
    limitation_keys = {
        "users": "users",
        "user_groups": "user_groups",
        "network_segments": "network_segments",
    }
    for _name, allowed in (("limitations", limitation_keys),):
        consume_scope(allowed=allowed)
    return True
"""
    )
    assert issues == []


def test_mutually_exclusive_branch_write_not_overwritten():
    """#846: if/else writes to one key are not sequential overwrites."""
    issues = _issue_kinds(
        """def make_payload(enabled: bool):
    payload = {"id": 1, "kind": "device", "source": "fixture"}
    if enabled:
        payload["status"] = "enabled"
    else:
        payload["status"] = "disabled"
    return payload
"""
    )
    assert issues == []


def test_sequential_unconditional_overwrite_still_flagged():
    """Guard: real dead stores must still be reported."""
    issues = _issue_kinds(
        """def f():
    d = {"a": 1}
    d["a"] = 2
    return d["a"]
"""
    )
    assert ("overwritten_key", "a") in issues

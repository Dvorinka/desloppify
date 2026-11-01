"""DictKeyVisitor — AST visitor tracking dict key writes/reads per scope."""

from __future__ import annotations

import ast

from desloppify.languages.python.detectors.dict_keys import (
    TrackedDict,
    _get_name,
    _get_str_key,
)
from .visitor_helpers import (
    analyze_scope_issues,
    mark_assignment_escape,
    mark_returned_or_passed,
    record_call_interactions,
)


class DictKeyVisitor(ast.NodeVisitor):
    """Walk a module AST, tracking dict key writes/reads per function scope."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._scopes: list[dict[str, TrackedDict]] = []
        self._nonliteral_names: list[set[str]] = []  # parallel to _scopes
        self._class_dicts: dict[str, TrackedDict] = {}  # self.x dicts
        self._in_class = False
        self._cond_depth = 0
        self._issues: list[dict] = []
        self._dict_literals: list[dict] = []  # for schema drift

    def _current_scope(self) -> dict[str, TrackedDict]:
        return self._scopes[-1] if self._scopes else {}

    def _track(
        self,
        name: str,
        line: int,
        *,
        locally_created: bool,
        initial_keys: list[str] | None = None,
    ) -> TrackedDict:
        scope = self._current_scope()
        td = TrackedDict(name=name, created_line=line, locally_created=locally_created)
        if initial_keys:
            for k in initial_keys:
                td.writes[k].append(line)
        scope[name] = td
        return td

    def _get_tracked(self, name: str) -> TrackedDict | None:
        # Check current scope first, then class scope for self.x
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        if name.startswith("self.") and name in self._class_dicts:
            return self._class_dicts[name]
        return None

    # -- Scope management --

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        self._scopes.append({})
        self._nonliteral_names.append(set())
        self.generic_visit(node)
        scope = self._scopes.pop()
        self._nonliteral_names.pop()
        self._issues.extend(analyze_scope_issues(self, scope, node.name))

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        prev_class_dicts = self._class_dicts
        prev_in_class = self._in_class
        self._class_dicts = {}
        self._in_class = True
        self.generic_visit(node)
        self._issues.extend(
            analyze_scope_issues(
                self,
                self._class_dicts,
                f"class {node.name}",
                is_class=True,
            )
        )
        self._class_dicts = prev_class_dicts
        self._in_class = prev_in_class

    # -- Dict creation --

    def visit_Assign(self, node: ast.Assign) -> None:
        if len(node.targets) == 1:
            target = node.targets[0]
            name = _get_name(target)
            if name:
                created = self._check_dict_creation(name, node.value, node.lineno)
                if not created:
                    # Bound to something we can't see — reads may be
                    # satisfied by external content (#846).
                    if self._nonliteral_names:
                        self._nonliteral_names[-1].add(name)
                    tracked = self._get_tracked(name)
                    if tracked:
                        tracked.provenance_unknown = True
        # Also check for subscript writes: d["key"] = val
        for target in node.targets:
            self._check_subscript_write(target, node.lineno)
        mark_assignment_escape(self, node.targets, node.value)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        # AugAssign (d["k"] += v) is both a read AND a write
        if isinstance(node.target, ast.Subscript):
            name = _get_name(node.target.value)
            if name:
                td = self._get_tracked(name)
                if td:
                    key = _get_str_key(node.target.slice)
                    if key:
                        td.reads[key].append(node.lineno)
                    else:
                        td.has_dynamic_key = True
        self._check_subscript_write(node.target, node.lineno)
        self.generic_visit(node)

    def _check_dict_creation(self, name: str, value: ast.expr, line: int):
        """Detect d = {}, d = dict(), d = {"k": v, ...}."""
        initial_keys: list[str] = []
        is_creation = False

        if isinstance(value, ast.Dict):
            is_creation = True
            for k in value.keys:
                sk = _get_str_key(k) if k else None
                if sk:
                    initial_keys.append(sk)
            # Collect dict literal for schema drift
            if (
                all(
                    isinstance(k, ast.Constant) and isinstance(k.value, str)
                    for k in value.keys
                    if k is not None
                )
                and len(value.keys) >= 3
            ):
                keys = [k.value for k in value.keys if isinstance(k, ast.Constant)]
                self._dict_literals.append(
                    {
                        "file": self.filepath,
                        "line": line,
                        "keys": frozenset(keys),
                    }
                )
        elif (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "dict"
        ):
            is_creation = True
            for kw in value.keywords:
                if kw.arg:
                    initial_keys.append(kw.arg)

        if is_creation:
            td = self._track(
                name, line, locally_created=True, initial_keys=initial_keys
            )
            if self._cond_depth:
                td.conditional_writes.add(line)
            if self._nonliteral_names and name in self._nonliteral_names[-1]:
                td.provenance_unknown = True
            # self.x dicts live at class scope — other methods may consume
            # them (#801). Analyzed once when the class visit completes.
            if name.startswith("self."):
                self._class_dicts[name] = td
        return is_creation

    def _check_subscript_write(self, target: ast.expr, line: int):
        """Handle d["key"] = val or d["key"] += val."""
        if not isinstance(target, ast.Subscript):
            return
        name = _get_name(target.value)
        if not name:
            return
        key = _get_str_key(target.slice)
        td = self._get_tracked(name)
        if td is None:
            return
        if key:
            td.writes[key].append(line)
            if self._cond_depth:
                td.conditional_writes.add(line)
        else:
            td.has_dynamic_key = True

    # -- Conditional regions (writes here aren't sequential overwrites) --

    def _visit_conditional_bodies(self, bodies: list[list[ast.stmt]]) -> None:
        for body in bodies:
            self._cond_depth += 1
            for stmt in body:
                self.visit(stmt)
            self._cond_depth -= 1

    def visit_If(self, node: ast.If) -> None:
        self.visit(node.test)
        self._visit_conditional_bodies([node.body, node.orelse])

    def visit_While(self, node: ast.While) -> None:
        self.visit(node.test)
        self._visit_conditional_bodies([node.body, node.orelse])

    def visit_Try(self, node: ast.Try) -> None:
        self._cond_depth += 1
        for stmt in node.body:
            self.visit(stmt)
        for handler in node.handlers:
            self.visit(handler)
        self._cond_depth -= 1
        for stmt in node.orelse + node.finalbody:
            self.visit(stmt)

    def visit_TryStar(self, node: ast.TryStar) -> None:
        self.visit_Try(node)

    def visit_Match(self, node) -> None:
        self.visit(node.subject)
        for case in node.cases:
            self._cond_depth += 1
            for stmt in case.body:
                self.visit(stmt)
            self._cond_depth -= 1

    # -- Dict reads --

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if isinstance(node.ctx, ast.Load):
            name = _get_name(node.value)
            if name:
                td = self._get_tracked(name)
                if td:
                    key = _get_str_key(node.slice)
                    if key:
                        td.reads[key].append(node.lineno)
                    else:
                        td.has_dynamic_key = True
        self.generic_visit(node)

    def visit_Delete(self, node: ast.Delete) -> None:
        for target in node.targets:
            if isinstance(target, ast.Subscript):
                name = _get_name(target.value)
                if name:
                    td = self._get_tracked(name)
                    if td:
                        key = _get_str_key(target.slice)
                        if key:
                            td.reads[key].append(target.lineno)
                        else:
                            td.has_dynamic_key = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        record_call_interactions(self, node)
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return):
        if node.value:
            mark_returned_or_passed(self, node.value)
        self.generic_visit(node)

    visit_Yield = visit_Return
    visit_YieldFrom = visit_Return

    def visit_Compare(self, node: ast.Compare) -> None:
        """Handle "key" in d."""
        for i, op in enumerate(node.ops):
            if isinstance(op, ast.In | ast.NotIn):
                comparator = node.comparators[i]
                name = _get_name(comparator)
                if name:
                    td = self._get_tracked(name)
                    if td:
                        # The left side of `in` for the first op is node.left
                        left = node.left if i == 0 else node.comparators[i - 1]
                        key = _get_str_key(left)
                        if key:
                            td.reads[key].append(node.lineno)
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        """Handle `for x in d` — bulk read; containers in iter escape (#846)."""
        name = _get_name(node.iter)
        if name:
            td = self._get_tracked(name)
            if td:
                td.bulk_read = True
        mark_returned_or_passed(self, node.iter)
        self.visit(node.target)
        self._visit_conditional_bodies([node.body, node.orelse])

    def visit_Starred(self, node: ast.Starred):
        """Handle {**d} or func(*d)."""
        name = _get_name(node.value)
        if name:
            td = self._get_tracked(name)
            if td:
                td.has_star_unpack = True
        self.generic_visit(node)

    # -- Dict literal collection (standalone, non-assigned) --

    def visit_Dict(self, node: ast.Dict) -> None:
        """Collect dict literals for schema drift analysis."""
        if (
            all(
                isinstance(k, ast.Constant) and isinstance(k.value, str)
                for k in node.keys
                if k is not None
            )
            and len(node.keys) >= 3
            and all(k is not None for k in node.keys)
        ):
            keys = frozenset(k.value for k in node.keys if isinstance(k, ast.Constant))
            self._dict_literals.append(
                {
                    "file": self.filepath,
                    "line": node.lineno,
                    "keys": keys,
                }
            )
        self.generic_visit(node)

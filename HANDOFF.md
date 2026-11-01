# Handoff — desloppify community fork continuation

## State
- Repo: `~/Desktop/PROG+HTML/desloppify`, branch `maint/continuation`, pushed to
  `Dvorinka/desloppify`. Summary PR #1 open (do not merge yet).
- Test env: `.venv` at repo root (`pip install -e ".[treesitter]" pytest`).
  Tree-sitter extras REQUIRED — many detector tests pass trivially without them.
- PORTS.md = triage ledger. CHANGELOG.md = delta vs upstream v1.0 (3a7735d).

## Session 2026-11-01 (II) — port batch progress
Committed+pushable on maint/continuation (push pending):
- Go: #887 golangci v2 cmd_fn, #643 flat-dir _test.go filter, #641 pkg.Recv.Name
  signature scoping, #642 already-fixed (3bac86a3). c5139d58.
- C#: #683 FQ-ref edges, #893 parse_member_bindings receiver edges,
  #892 "unknown" quality + broader asserts, #726 verified via #890. cb67b132.
- Rust: #824 _preceding_metadata multiline-attr walk, #756 _cargo_target_paths
  entry roots (+ entry_patterns_fn on make_cmd_orphaned). 70390b7f.
- cxx/bash: #903 keyword reject + owner-qual names + type-normalized params,
  #866 covered-header→same-stem-impl promotion, #873 verified (4fa23bba),
  #806 shellcheck per-file -print0. 7d32ba80.
- #786 log_sensitive payload-aware + schema-validated json_parse. 1c91976d.
- #709 next_lint→eslint on next>=16 (cmd_resolver). d8267ca0 (pushed).

## Session 2026-11-01 (III) — detector queue DRAINED
Committed on maint/continuation:
- #858 TS resolver parity: `~/` joins `@/` in tsconfig fallback (declared
  wins); resolve_import_spec shares iter_resolve_candidates (.js stems).
  memo-ri repro unrecoverable (repo deleted) — proven via synthetic repro.
  9c7767fe.
- #907 py scan-root import mapping (unambiguous suffix match) + windows
  \\ -> / graph normalization + coverage potential label. a5d9059b.
- #905 importlib file-load paths (spec_from_file_location,
  SourceFileLoader, load_source) count as test imports. a8e83d7a.
- #801/#846 dict_keys provenance: self.x -> class scope analysis, escape
  + nonliteral rebinding -> provenance_unknown (no phantom), conditional
  writes need 2 unconditional for overwritten_key, for-iter escapes.
  06425626.
- #771 *_selftest.py Zone.TEST + X_selftest->X.py naming. 1798e943.
- #758 has_inline_tests: selftest fn + __main__/argv wiring = coverage.
  3a1125af.

## Remaining PORT rows
- TRACK (61): deep queue/plan machinery bugs — untouched by design.

## Immediate next work
1. Push maint/continuation; refresh PR #1 body with final delta.
2. TRACK queue when owner wants machinery work.
3. CHANGELOG is current; PORTS all rows resolved to DONE/SKIP/TRACK.

## Learned pitfalls
- `desloppify/data/global/SKILL.md` must equal `docs/SKILL.md` (bundled-sync test).
- `save_state` recomputes scores — stamp `strict_score` etc. by patching JSON directly.
- `load_state` reconstructs from plan.json when scan_source != "scan" — set `last_scan`.
- CLI flag order: `desloppify --lang X scan ...` (global flag, not subcommand flag).
- Commits need `Authored By: TDvorak <info@tdvorak.dev>` trailer.
- FunctionInfo.name for methods is now owner-qualified in Go (pkg.Type.Name)
  and cxx (A::Method) — signature-variance groups correctly.
- make_tool_phase gains cmd_fn(Path,lang)->str|None (per-call cmd override;
  used by golangci v2). Framework ToolIntegration has cmd_resolver (nextjs).
- parse_file_symbols (csharp) returns a 4-tuple now (adds qualified_refs).

## Verified on Invico
`desloppify --lang typescript scan --path apps/web --profile ci --no-badge` works —
reads upstream-written `.desloppify` state fine, preserved plan/baseline, scores.

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

## Session 2026-11-01 (IV) — review cost modes + TRACK batch
Committed on maint/continuation:
- feat(review): `--batch-mode grouped|single` for `review --run-batches`
  — collapse ~20 per-dimension subagent runs to ~9 (evidence-collector
  groups) or 1. run_summary.json records batch_mode; --import-run
  replays grouping. Prompt pluralizes multi-dim batches. 20214ae7.
- #906 skipped assessments filtered from postflight partitions,
  #919 resolve guard mirrors cluster-focus view, #928/#929 backlog
  dedupes canonical ids, #930 cluster add refuses skipped ids,
  #931/#701 auto_complete_steps only completes when refs absent from
  plan AND not open in state. 6871a47e.
- #780 next/backlog --state load sibling plan via plan_path_for_state.
  909d1d3a.
- #727 auto-detect fallback/multi-candidate file count now honors
  DEFAULT_EXCLUSIONS + configured excludes; C# detect_markers widened to
  .sln/.slnx/.csproj/.fsproj/Directory.Packages.props. e6002187.

## Remaining PORT rows
- TRACK (~50 left): machinery bugs — next likely: #855 stale reopened
  metadata, #784 reflect defer vs validation, #863 strict score vs
  auto_resolved (design decision — penalizes scan-confirmed resolutions;
  verify intent before changing), #872 unchanged-finding re-review loop
  (intentional per upstream test — document, don't fix), #727/#700
  #700 Xcode-as-TS (needs zero-source-file scan policy — detection
  alone can't fix a Swift-only project since swift is unregistered).
  Then strategist/triage-prompt cluster.

## Immediate next work
1. TRACK queue remainder per above ordering.
2. Refresh PR #1 body when queue drains further.

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

## Session 2026-11-01 (V) — TRACK machinery batch II
Committed on maint/continuation:
- #855 reconcile restores skip-kind status AND cleans stale reopen
  metadata (note/resolved_at/attestation/reopen_count from skip entry).
  52322257.
- #784 staged reflect prompts no longer leak strategist defer/break_up
  vocabulary — upstream PR #637 ported (include_auto_cluster_decision_
  guidance flag). 8e893135. Also resolves #884 (same defect).
- #780 follow-up: plan_path_for_state coerces str→Path. 23a47730.
- #700 zero-reviewable-file policy: warn_no_reviewable_files fires on
  ANY zero-production-file scan (auto-detect too); build_subjective_
  items returns [] when zone_distribution has no production or
  codebase_metrics total_files=0. b71152c1.
- #863 ported upstream PR #751: resolution_kind {file_deleted,
  zone_policy} exempt from strict; inferred auto_resolved still fails
  (intentional per #309). scoring.md documented. c8be04ab.
- #872 intentional (upstream test asserts wontfix→stale) — documented
  in SKILL.md key concepts. 44b49ecc.
- #882 strategy::* upsert preserves lifecycle evidence; closed items
  get proper strategist_reopen transition. 641a9a37.
- #883 recent_investment windowed to score trajectory; untimestamped
  resolutions not guessed recent. dbbe6807.
- #900 PARTIAL: detector→dimension map wired into backlog/recent_
  investment/rework; completed_clusters falls back to
  execution_status=done clusters; printed hints use --add-step.
  3e9027f3. REMAINING: strategy:: ids sit in queue_order but next
  shows "0 items" (synthetic prefix filtered — needs execution-queue
  routing), cmd_plan_resolve logs done before guards, enrichment gate
  hits already-done clusters, mixed operation/issue counting.

## Remaining PORT rows
- #888 (step-count contradiction + subjective/objective queue
  deadlock) — next priority.
- Rest of triage cluster: #826 #825 #823 #821 #815 #813 #809 #805
  #785 #779 #759 #754 #898 #845 #832 #830 #827 #908, then PR rows.

## Session 2026-11-01 (VI) — #888 partial
- #888 part 1 done: unenriched_clusters accepts consolidated steps when
  step issue_refs cover every member (fixes prompt↔validator
  contradiction). 7c2562b7.
- #888 part 2 OPEN: subjective/objective queue deadlock — next picks
  mechanical cluster, plan resolve refuses because subjective::X is
  current next item, review refuses because objective findings open.
  Needs queue-ordering/routing work in _work_queue.

## Session 2026-11-01 (VII)
- #827 commit records now attribute the unique owning cluster;
  ambiguous stays null. bf276c8c.

## Session 2026-11-01 (VIII)
- #845 summary_hash→id index resolves holistic citations/verdicts in
  observe (citation count, YAML verdict parse, short-hash resolution).
  23098f74.

## Session 2026-11-02 (IX) — upstream PR #881 ported
- Applied upstream #881 via git apply --reject; resolved ~10 .rej files
  (most were already-merged content). Suite 6356 passed; only the two
  known environmental dry-run failures remain.
- Canonical skip freshness: only an active exact-ID false_positive skip
  suppresses review refresh. merge_scan_results loads canonical FP ids,
  passes them to upsert (raw reopen kept, evidence suppressed only for
  canonical FP), and runs reconcile_plan_after_scan inside the state lock
  before saving, so dispositions persist for reopen-cycle counting.
  runtime.state now updated in place (clear+update) so caller-held rows
  stay visible.
- Fork-lock adaptation: reconstruct_state_from_saved_plan restricts skip
  restoration to false_positive-kind entries (restore_kinds param;
  non-FP kinds must not fabricate pre-merge defunct rows or reappearances
  never count as evidence). repair_state path still restores all kinds.
  When the locked reload is a plan reconstruction, merge adopts the
  runtime work_items/issues/scan_count/last_scan (reconstruction is
  strictly less informed).
- workflow merge saves the raw merged state through the module
  save_state before the in-lock canonical reconciliation (upstream save
  ordering, observable two-phase). Restored imports dropped by the
  port's rej merge (_reconcile_plan_post_scan_impl,
  resettable_default_dimensions) — these had silently broken
  tests/scan integration paths.
- Ported test test_app_canonical_skip_freshness.py (14 cases) — one
  fork-contract adaptation: absence-after-same-second re-reads the row
  after the second run (state round-trips through disk between scans).
- #881 committed this session; PORTS.md rows updated (#881 #844 #880
  #877 #850 #840 #891 #935 #937 #870 DONE).
- Commit: fix: preserve review freshness and queue prerequisites (#881)

## Session 2026-11-02 (X) — #888 queue deadlock closed
- #888 part 2 done: assessment-postflight phase now fronts
  cluster-queued mechanical work (multi-member manual clusters) ahead
  of the stale review marker when no postflight_scan_completed marker
  is recorded; marker stays visible behind. Fixes the next ↔
  plan-resolve ↔ review-rerun deadlock: all three see the same front.
- Gate narrowed to cluster-fronted items after two fork-authored tests
  pinned the old contract: lone queued findings stay parked (resolvable
  by id via the guard's front-planned branch; parked objective items do
  not block the rerun gate). _clustered_execution_items filters
  anchored items to non-auto clusters with >=2 members.
- Regression tests: queued cluster fronts queue + collapse shows
  cluster before marker; empty queue keeps marker-only partition.
- Suite: 6358 passed, 2 known dry-run env failures. Commit 973c6a7b.
- Next: #900 remaining parts (strategy:: visibility, log ordering,
  done-cluster enrichment gate, mixed counting), then triage cluster
  #830 #826 #825 #823 #821 #815 #813 #809 #805 #785 #779 #759 #754
  #908 #832, then meta rows #686 #658/#650 #744.

## Session 2026-11-02 (X continued) — #900 remaining parts
- strategy:: visibility: new is_marker_id predicate (triage/workflow/
  subjective) splits phase markers from persisted work. live_planned_queue_ids,
  live_planned_queue_empty, refresh_lifecycle._is_real_queue_issue,
  scan_issue_reconcile reference sets, and _reset_cycle_for_force_rescan
  now treat strategy:: ids as real work — queued strategy items execute
  through next and survive force-rescan. Strategist-created items get
  file="." so non-root scan scopes cannot drop them.
- Enrichment gate: unenriched_clusters skips clusters marked done whose
  members all stayed resolved; a reopened member re-gates the cluster.
  Two legacy-scope tests updated to keep the fixture executable.
- Mixed counting: execution_pattern_analysis now reports *_operations
  (log entries) vs *_issues (distinct real ids — cluster fronts expand
  via plan membership, globs and marker ids excluded). Takes plan for
  expansion; callers updated.
- Log ordering (#900 complaint) was already fixed by #922 (773e54c6).

## Session 2026-11-02 (X continued) — #825 + #813 closed
- #825: organise op-minimum and report-reference checks now use
  scoped_manual_clusters_with_issues (live slice); structure sense-check
  prompt re-scopes the reloaded plan so done clusters can't re-enter
  the dependency graph. 8e9234e2.
- #813: postflight suppression of subjective dims now requires the
  covering review issues to be executable — stale/never-run triage
  masking no longer empties `next` while plan queue lists refresh ids.
  String-detail legacy items guarded. 3cff7831.
- Next: #830 #826 #823 #821 #815 #809 #805 #785 #779 #759 #754 #908 #832.

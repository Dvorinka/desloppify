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

## Session 2026-11-02 (X continued) — #830 closed
- #830: resolution scope for partial imports is now bounded by the
  packet's declared dimensions — ReviewImportConfig.allowed_dimensions
  threaded through do_import; import_holistic_issues intersects the
  collected scope with it. Stray payload dims can no longer resolve
  holistic findings the batch never covered. 4dc9839b.
- Next: #826 #823 #821 #815 #809 #805 #785 #779 #759 #754 #908 #832.

## Session 2026-11-02 (X continued) — #830 + #826 closed
- #830: ReviewImportConfig.allowed_dimensions bounds partial-import
  resolution to the packet's declared dims — stray payload dims can no
  longer resolve holistic findings the batch never covered. 4dc9839b.
- #826: review --prepare now rewrites .desloppify/review_packet_blind.json
  from the freshly built payload — structure profiles are derived data
  and can no longer go stale while scan refuses mid-cycle. 4c57f81f.
- Next: #823 #821 #815 #809 #805 #785 #779 #759 #754 #908 #832.

## Session 2026-11-02 (XI) — upstream PR/issue sweep started
- Ported upstream PR #912 (Kotlin import graph from packages) and #939
  (-lc -> -c) cleanly via git apply. 09556943.
- New upstream issues to track: #944 #943 #942 #941 #940 #936 #934 #933
  #932 #931 #930 #929 #928 #927 #923 #921 #919 #918 #917 #916 #915 #909
  (and #908 already TRACK).
- Open upstream PRs still to port (diffs saved /tmp/opencode/pr*.diff,
  need manual rej merges): #890 C# deps, #897 relative scan roots,
  #899 cxx api matches, #901 cxx response-file includes, #904 abs
  exclude dirs, #910 cxx AST langs, #911 autofix per file, #913 Kotlin
  unused imports, #914 excluded/gitignored paths, #920 JS import edges,
  #924 TS importer config aliases, #925 test coverage aliases, #926
  Next.js entrypoints, #938 detector evidence for scan verification.
  #902 license change — skip (non-mechanical/legal).
- Multi-repo queue from user: after desloppify ports, resolve
  Dvorinka/cloudreve issues #412 #369 + PRs #414 #413; then
  Dvorinka/Nothing_Modes — fix SQLiteFullException crash reports inside
  PR #42, add to PR, merge/release it; then run desloppify on
  Nothing_Modes only, write findings file to workspace (NO fixes), and
  release the PR.

## Session 2026-11-02 (XI cont.) — upstream PR sweep COMPLETE
- All upstream PRs accounted for: ported this session #912+#939
  (09556943), #913 (a10f89d3 manual merge). Already ported earlier:
  #890 bb106605, #897 covered by #904's a097d5e8, #899 89702e62,
  #901 61bd10f3, #904 a097d5e8, #910 9a27b838, #911 9ab412e3,
  #914 a7fd9417, #920 98bd2658, #924 36dfaf86, #925 324811f2,
  #926 1fe39165, #938 243638ba. #902 (Apache relicensing) skipped —
  non-mechanical legal change.
- New issues #909-#936 already adjudicated in PORTS.md.

## Remaining desloppify queue (in order)
1. #944 TS scans miss JS/.mjs tests incl root-level test dirs —
   TypeScriptConfig.test_file_extensions only .ts/.tsx; extend coverage
   discovery to .js/.jsx/.mjs/.cjs tests at root AND subdir scans without
   widening production source scope. See PR #783 for symmetric fix.
2. #943 generic autofix no-op: autofix cmd.py calls fixer.fix(entries,
   dry_run) WITHOUT path= -> generic fixer returns previews counted as
   successes; must fail closed + pass scan root through fixer protocol.
   Also apply_retro.py same omission. Also: dry-run prints findings as
   "files"; infers fixed entries from count diff; drops scan excludes.
3. #942 Swift Tests dirs classified production — SwiftPM Tests/<T>Tests/
   vs case-sensitive /tests/ zone rule. Prefer Swift-specific Tests rule.
4. #941 TS duplication jscpd fails in pnpm-only devEngines workspaces —
   npx evaluates devEngines; run jscpd isolated from target workspace or
   honor configured package manager.
5. #940 Lua unused_import flags string literals (load modes, pack
   formats, table keys) + suppress pattern detector::*::rule can't match
   IDs with ::line suffix (needs trailing ::*).
6. #908 blind review prompts leak prior subjective scores (TRACK).
7. Backlog TRACK: #832 #823 #821 #815 #809 #805 #785 #779 #759 #754;
   meta rows #686 #658/#650 #744.

## Session 2026-11-02 (XII) — #944 closed
- #944 verified already-fixed in fork: the #844 port (ecaebee7) carried both
  halves — `TypeScriptConfig.test_file_extensions` widened to
  .ts/.tsx/.js/.jsx/.mjs/.cjs and `_find_external_test_files` no longer skips
  in-scan test dirs (it searches only extensions absent from the production
  inventory, so no double-count and no production-scope widening;
  TS_EXTENSIONS still .ts/.tsx). Upstream's issue predates that merge.
- Added the issue's requested production-phase regression test:
  tests/lang/typescript/test_ts_external_js_test_discovery.py — real
  phase_test_coverage + real TypeScriptConfig + FileZoneMap on a tmp project,
  parametrized .js/.jsx/.mjs/.cjs × root/subdir scans; asserts the JS-tested
  module is covered and an unrelated module stays flagged. Mutation-checked:
  reverting the extension list reproduces the bug (value.ts flagged).
- Next: #943 #942 #941 #940 #908, then TRACK backlog.

## Session 2026-11-02 (XII cont.) — #943 closed
- Core already fixed by the #911 port: cmd.py passes path via
  takes_scan_path, make_generic_fixer fails closed without it, dry-run
  counts unique files, recheck-fail claims nothing. Verified.
- Remaining gap fixed: apply_retro._cascade_unused_import_cleanup invoked
  fix() without path — same omitted-path call the issue flags; for generic
  fixers it now raised instead of silently passing. Now mirrors the
  takes_scan_path protocol.
- Regression test: test_cascade_passes_scan_path_to_generic_fixer drives a
  real make_generic_fixer through the cascade with an injected runner and
  asserts all three tool invocations run with cwd=scan path.
- Deferred (upstream-accepted trade-offs, noted): fixed entries inferred
  from per-file count diff rather than diagnostic matching; fix_cmd runs
  at scan root without forwarding excludes — no ToolSpec field exists for
  per-tool exclude flags.
- Next: #942 #941 #940 #908, then TRACK backlog.

## Session 2026-11-02 (XII cont.) — #942 closed
- Swift zone rules: `ZoneRule(Zone.TEST, ["/Tests/"])` prepended to
  generic_zone_rules in languages/swift/__init__.py — segment-bounded
  (matches Tests/ dirs incl. nested packages, not Contests/ or Tests.swift).
  Chose the Swift-specific rule per the issue's hint over global case-folding.
- Regression: tests/lang/swift/test_swift_zones.py — 8 cases incl.
  Packages/Foo/Tests/ nesting and production controls.
- Next: #941 #940 #908, then TRACK backlog.

## Session 2026-11-02 (XII cont.) — #941 closed
- jscpd isolation: _run_jscpd_command gained cwd kwarg; detect_with_jscpd
  now runs npx/jscpd from the neutral output tempdir, so npm never
  evaluates the target workspace's devEngines (EBADDEVENGINES fix).
  Scan arg resolved absolute so the detached cwd can't break it.
- _to_scan_relative now also tries scan_root/name for relative report
  names — tolerant if jscpd emits scan-relative paths.
- Regression: test_runs_jscpd_from_isolated_cwd (cwd!=workspace, absolute
  scan arg), test_parses_scan_relative_report_names.
- Chose isolation over honoring devEngines (no pnpm/dlx detection needed).
- Next: #940 #908, then TRACK backlog.

## Session 2026-11-02 (XII cont.) — #940 closed
- Lua FP: LUA_SPEC.import_query matched ANY function_call with a string
  arg (load modes, string.pack formats, assert messages, table keys).
  Constrained with (#eq? @_fn "require") — bare `require "mod"` shares
  the same node shape, so one pattern covers both forms.
- Suppress glob: matched_ignore_pattern now retries ::-patterns with an
  implicit "::*" tail, so the documented `detector::*::rule` form matches
  IDs carrying a ::line suffix. File globs and prefix forms unchanged.
- Regression: tests/lang/common/test_lua_unused_imports.py (4 cases),
  tests/state/test_matched_ignore_pattern.py (7 cases).
- Next: #908, then TRACK backlog.

## Session 2026-11-02 (XII cont.) — #908 closed
- Blind-review leak: `desloppify show` printed an AGENT PLAN footer +
  subjective followup (prior dimension scores) after mechanical output.
  Added `show --blind`: skips show_agent_plan, show_subjective_followup,
  and _render_subjective_views_guide. prompt_sections.py now emits
  --blind on every suggested `desloppify show` navigation command.
- Regression: test_show_blind_suppresses_plan_and_score_footer verifies
  all three footers are skipped under --blind and fire without it.
- Next: TRACK backlog #832 #823 #821 #815 #809 #805 #785 #779 #759 #754,
  meta #686 #658/#650 #744.

## Session 2026-11-02 (XII cont.) — #832 closed
- Already fixed in fork: cli.py sets runtime.plan_file =
  plan_path_for_state(--state) and get_plan_file honors it, so
  next/plan --state X read the sibling plan. Verified end-to-end;
  pinned with test_load_plan_honors_runtime_plan_file_override.
- Next: #823 #821 #815 #809 #805 #785 #779 #759 #754, meta rows.

## Session 2026-11-02 (XII cont.) — #823 closed
- _write_desloppify_cli_helper now takes the run args and bakes explicit
  --lang (global flag, before "$@") and --state (subcommand flag, after
  "$@") into run_desloppify.sh. Helper-issued show/plan/next commands in
  mixed-language workspaces now hit the same state file as the triage run.
- Regression: test_cli_helper_bakes_in_explicit_lang_and_state +
  unchanged-behavior control.
- Next: #821 #815 #809 #805 #785 #779 #759 #754, meta rows.

## Session 2026-11-02 (XII cont.) — #821 closed
- phase_boilerplate_duplication now records reduced DetectorCoverageStatus
  on jscpd failure — score flagged incomplete instead of full coverage.
- workflow._restore_failed_detector_potentials preserves the previous
  potential entry for reduced detectors that produced none this run, so
  retained findings still contribute (no spurious improvement).
- Regression: tests/commands/scan/test_failed_detector_potentials.py (4).
- Next: #815 #809 #805 #785 #779 #759 #754, meta rows.

## Session 2026-11-02 (XII cont.) — #815 closed
- Already fixed by the same sibling-plan mechanism as #832: review import
  resolves plan via plan_path_for_state(state_file) (importing/cmd.py:228,
  plan_sync.py:441) and next/plan read the same sibling plan via
  runtime.plan_file. Per-language --state files → isolated execution
  queues; imports can no longer purge other languages' work.
- Next: #809 #805 #785 #779 #759 #754, meta rows #686 #658/#650 #744.

## Session 2026-11-02 (XIII) — #809 closed
- Already fixed in fork: the #938 port (243638ba) added ran_detectors to
  find_suspect_detectors and confirmed_detectors gating in
  verify_disappeared, so a review-only merge (potentials={review,concerns})
  skips mechanical items entirely. Issue's minimal repro now returns
  (0,0,0,set()) with the item unchanged.
- Fresh-assessment staleness also impossible: review/concerns lack
  marks_dims_stale, so import changed_detectors cannot reach
  _mark_stale_on_mechanical_change.
- Covered by existing tests test_review_import_does_not_verify_mechanical_issue
  (fixed/wontfix/false_positive + assessment stays fresh) and
  test_review_import_preserves_mechanical_disposition (suspect set + later
  real scan verifies normally). Issue's exact repro pinned — no new test
  needed beyond existing parametrization.
- Next: #805 #785 #779 #759 #754, meta rows #686 #658/#650 #744.

## Session 2026-11-02 (XIII cont.) — #805 closed
- Already fixed in fork: enforce_trusted_import_coverage_gate only blocks
  when the packet's selected dims are missing (upstream #935 port,
  fa91641c); the coverage notice itself is computed against
  packet_dimensions, not language-wide scored dims (upstream #840 port,
  7eefcfd2, comment in execution_results.py names the exact scenario).
- Existing tests cover it: explicit 18/20 subset passes, missing selected
  dim blocks, full default selection stays fail-closed
  (test_selected_dimension_coverage.py).
- Next: #785 #779 #759 #754, meta rows #686 #658/#650 #744.

## Session 2026-11-02 (XIII cont.) — #785 closed
- Ordering fix: _apply_persisted_exclusions now runs in main() before
  _resolve_default_path and _load_shared_runtime (previously state_path
  and default-path detection ran pre-exclusion while the scan handler's
  resolve_lang ran post-exclusion — state file and detector language could
  disagree). _load_shared_runtime takes config= to avoid a second
  load/print.
- Regression: tests/commands/test_exclusion_language_ordering.py — mixed
  package.json+Makefile project with cxx sources under excluded deps/;
  asserts pre-exclusion detection picks cxx, post-exclusion picks
  typescript, and runtime state path binds state-typescript.json.
- Newly observed PRE-EXISTING suite failures (clean tree, unrelated):
  test_run_codex_pipeline_raises_on_stage_failure (triage split modules),
  test_phase_boilerplate_duplication_handles_none_and_entries (AttributeError
  in shared_phases_helpers.py:185). Add to known-env-failure list.
- Next: #779 #759 #754, meta rows #686 #658/#650 #744.

## Session 2026-11-02 (XIII cont.) — #779 closed
- Same defect as #805: 13-dim selected run-batches import blocked for the
  7 unselected dims. Already fixed — packet_dimensions is normalized from
  the immutable packet's declared dims and the gate only blocks on
  selected-dim misses (#935+#840 ports).
- Next: #759 #754, meta rows #686 #658/#650 #744.

## Session 2026-11-02 (XIII cont.) — #759 closed
- Root cause: merge_scan appends scan_history with pre-adjudication scores;
  the canonical FP restore + lock-exit save recompute later mutate the
  persisted top-level, so history/output (28.0) disagreed with state (30.5).
- Fix: _sync_scan_history_scores in scan/workflow.py recomputes stats after
  all in-lock mutations (potentials restore, mark_stale_holistic,
  reconcile_plan_after_scan) and rewrites the appended entry's score/open/
  dimension fields; runtime.state sync then picks up the final values, so
  printed output, history, and disk all agree.
- Regression: test_scan_history_scores_match_persisted_state in
  test_app_canonical_skip_freshness.py — asserts history[-1] equals
  persisted top-level across all score fields; fails pre-fix (28.0 vs 30.5).
- Next: #754, meta rows #686 #658/#650 #744.

## Session 2026-11-02 (XIII cont.) — #754 closed
- Complaint 1 (contradictory requirements) already resolved: unenriched_clusters
  only needs description + >=1 step (#888 consolidated-step coverage), the
  rendered requirements text says "consolidate related issues into one step",
  and the >1.0 step-ratio warning is advisory for >=3-issue clusters only.
- Complaint 2 (exit 0 on refusal) fixed: _cmd_stage_organize now raises
  CommandError(exit 1) when the reflect prerequisite fails or submission
  validation refuses, instead of returning silently — runner subprocesses
  can detect rejection. No-queue early return stays exit 0 (vacuous).
- Regression: test_organize_exits_when_reflect_requirement_not_met updated
  to expect CommandError; new test_organize_raises_when_submission_validation_fails
  asserts a short report refuses and records no stage.
- Next: meta rows #686 #658/#650 #744.

## Then: Dvorinka/cloudreve
- Issues: #412 (4.19.1 Docker image vulns — Go toolchain/modules/Alpine),
  #369 (upstream watch). PRs: #414 Android 2FA login+dark-mode form,
  #413 no auth token on presigned object-storage URLs. Review + merge.

## Then: Dvorinka/Nothing_Modes (user-prescribed order)
1. Fix crash reports FIRST: android.database.sqlite.SQLiteFullException
   code 13 in Room endTransaction (d5.b.e / androidx.room.w.b, worker
   dispatcher) on app 0.19.11, Infinix X6725. Likely cause: unbounded
   Room writes (cache/history table) + no disk-space handling — add
   bounded retention/cleanup + SQLITE_FULL catch so it degrades.
2. Add fix to open PR #42 (feature/onboarding-guide — onboarding,
   starter modes, BT control, reviewer fixes), resolve + merge it.
3. Run desloppify on Nothing_Modes repo ONLY.
4. Write all findings to a file in the workspace — do NOT fix any.
5. "Release the pr" (merge/release per repo convention).

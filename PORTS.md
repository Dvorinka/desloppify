# PORTS — upstream triage ledger

Audit of `peteromallet/desloppify` open/closed issues and PRs as of 2026-11-01,
against fork HEAD `3a7735d` (v1.0). Verdicts:

- **PORT** — real fix worth taking into the fork (queued or ported; ported items are ticked).
- **DONE** — already fixed/equivalent in this codebase.
- **SKIP** — out of scope for this fork: Windows-only runner bugs, external-runner
  (codex/opencode/rovo) plumbing, languages we don't exercise, or cosmetic.
- **TRACK** — valid bug, but touches deep queue/plan machinery; revisit after the
  core detector fixes settle.
- **PENDING** — port attempted but conflicts under `git apply --3way` with the
  ported tree; needs a hand-merge, not mechanical application.

## Issues

| Issue | Verdict | Note |
|---|---|---|
| #936 coverage scan log labels denominator wrong | SKIP | log cosmetics |
| #934 review defaults to missing src when scan_path null | DONE | get_default_scan_path falls back to root (fix g) |
| #933 TS coverage/dep resolvers miss workspace exports | DONE | resolvers follow workspace exports (2b7120d1) |
| #932 next recommends dead-useeffect autofix for README finding | SKIP | nudge wording |
| #931 queued work auto-completes unrelated steps | DONE | step refs stay pending while open in state (6871a47e) |
| #930 plan cluster add crashes on protected skip | DONE | add_to_cluster refuses skipped ids upfront (6871a47e) |
| #929/#928 backlog duplicate IDs / repeats findings | DONE | backlog dedupes canonical IDs across partitions (6871a47e) |
| #927 move misses imports with explicit TS extensions | DONE | specifier-form variants in move (e4fd165a) |
| #923 CLI threatens target-match resets though policy disabled | DONE | fixed here — threat text aligned with disabled policy (fix e) |
| #922 plan resolve exits 0 on queue-order guard reject | DONE | CommandError exit 1 + done-log moved after guard |
| #921 test-coverage summary labels LOC potential wrong | SKIP | display |
| #919 cluster resolve rejects cluster shown by next | DONE | guard mirrors next's cluster-focus view (6871a47e) |
| #918/#917 Windows triage UTF-8 / npm codex.cmd quoting | SKIP | Windows runner |
| #916 relative scan roots → relative Bandit exclusions | DONE | ported #897+#904 absolute exclusion dirs |
| #915 Python dynamic import discovery ignores exclusions | DONE | find_py_files now used |
| #909 Windows JS dep graph zero import edges | SKIP | Windows tree-sitter |
| #908 blind review prompts leak prior subjective scores | TRACK | review pipeline |
| #907 Python external-test mapping loses import roots | DONE | scan-root suffix match + windows sep normalization + potential label (a5d9059b) |
| #906 skipped assessments select empty next queue | DONE | skipped filtered from postflight partitions (6871a47e) |
| #905 Python coverage misses importlib hyphenated CLIs | DONE | spec_from_file_location/SourceFileLoader/load_source .py literals |
| #903 C++ signature variance false compares | DONE | keyword reject + owner qualifier + type-normalized params |
| #900 strategist history schema drift | DONE | 3e9027f3 dim mapping + done clusters + step hints; log ordering covered by #922 (773e54c6); 296973df — strategy:: ids are live queue work (is_marker_id), enrichment gates only executable clusters, execution log splits operation vs issue counts |
| #898 cluster-name resolution vs member IDs | DONE | 2c1e5733 |
| #894 (closed) scan reopens adjudicated findings | DONE upstream | |
| #893 C# inferred property receivers → transitive_only | DONE | parse_member_bindings receiver edges |
| #892 C# custom test runners → no_tests | DONE | "unknown" quality + broader assert spellings |
| #888 triage step-count / queue deadlock | DONE | 7c2562b7 step-count via issue_refs coverage; 973c6a7b assessment-postflight fronts cluster-queued mechanical work ahead of the stale review marker when no postflight scan is recorded |
| #887 Go scanner invokes removed golangci-lint v1 flag | DONE | cmd_fn picks v2 flag by installed major |
| #886 Windows Codex batch quoting/locale | SKIP | |
| #885 C# field names flagged as secrets | DONE (class) | covered by value-based secret gate (fix b) |
| #884 clarify defer disposition in triage prompts | DONE | 8e893135 — same defect as #784; defer removed from staged contract (skip = retains backlog) |
| #883 strategist recent_investment counts lifetime | DONE | dbbe6807 — windowed to trajectory |
| #882 repeated strategist identifiers erase evidence | DONE | 641a9a37 — upsert preserves lifecycle, proper reopen |
| #873 duplicate detector compares nested callbacks to container | DONE | already fixed — overlapping spans skipped (4fa23bba) |
| #872 accepting unchanged findings schedules another review | DONE | 44b49ecc — intentional; documented in SKILL.md |
| #867 cppcheck batching → cross-batch unused FPs | DONE (class) | covered by ported #869 whole-program pass |
| #866 C++ test import mapping behind headers | DONE | covered header promotes same-stem impl |
| #863 strict score penalizes auto_resolved | DONE | c8be04ab — intentional for inferred; file_deleted/zone_policy exempted (PR #751 port) |
| #859 C++ orphan detector misclassifies Unreal modules | SKIP | Unreal-specific |
| #858 TS coverage transitive_only for rendered components | DONE | ~/ + .js specifier resolver parity (9c7767fe); memo-ri repro unrecoverable (repo deleted) — gap proven via synthetic repro |
| #856 codex --scan-after-import blocked by new queue | DONE (class) | `--rescan` is the sanctioned bypass (fix f) |
| #855 plan skip restoration leaves stale reopened metadata | DONE | 52322257 |
| #854 lru_cache_mutable flags immutable ctor globals | DONE | |
| #853 Python unused detector silent zero without Ruff | DONE | missing-tool coverage |
| #849 Python orphan misses Alembic runtime modules | DONE | |
| #847 mixin contract misses inherited methods | DONE | |
| #846/#801 dict_keys FPs for fallbacks/aliases | DONE | provenance/conditional/self-scope fixes |
| #845 observe triage: holistic issues can't be cited by hash | DONE | 23098f74 |
| #842 RequestInit credentials flagged as secret | DONE (class) | value-based gate (fix b) — `credentials: "include"` has no secret value |
| #838 TS props detector counts union alternatives | DONE | member-line counting (60c61251) |
| #832 next/plan ignore plan dir implied by --state | TRACK | |
| #831 TS unused ignores tsconfig.json | DONE | nearest-tsconfig walk (ported #713, 99e0c2a3) |
| #830 partial trusted review import resolves outside dimension | TRACK | |
| #829 schema-drift clustering quadratic | SKIP | perf |
| #827 CLI commit records omit cluster attribution | DONE | bf276c8c |
| #826 blind packet structure profiles go stale | TRACK | |
| #825 triage includes inactive historical clusters | TRACK | |
| #824 Rust multiline attributes hide annotations | DONE | metadata walk crosses `)]` tails |
| #823 triage runner loses language/state in mixed projects | TRACK | |
| #821 boilerplate detector drops scoring potential | TRACK | |
| #815 mixed-language review imports remove queue items | TRACK | |
| #814 Python coverage misses runpy.run_path tests | DONE | .py literal specs from runpy.run_path args |
| #813 post-flight refresh in queue but next empty | TRACK | |
| #811 sort_no_comparator warns on canonical ordering | DONE | string-keyed Object sources exempt (d1205d5c) |
| #810 TS async_no_await mistakes return types for bodies | DONE | signature-brace tracking (ported #721, d5b770e5) |
| #809 review imports scan-verify + stale fresh assessments | TRACK | |
| #808 PyPI 1.0 locale-dependent Codex decoding | SKIP | Windows |
| #807 scan prints conflicting pre/live scores | SKIP | output |
| #806 multi-file ShellCheck can crash silently | DONE | per-file -print0/-0/-n 1 invocation |
| #805 targeted re-review requires unselected dims | TRACK | |
| #787 recovered queue item requests scan the guard rejects | DONE (class) | `--rescan` (fix f) |
| #786 security detector FPs for static logs/JSON parsing | DONE | payload-aware log_sensitive + schema-validated json_parse |
| #785 scan persists to wrong language state on exclusion change | TRACK | |
| #784 reflect permits defer but validation rejects it | DONE | 8e893135 — upstream PR #637 port |
| #780 next --state loads wrong plan | DONE | sibling plan via plan_path_for_state; backlog same (909d1d3a) |
| #779/#779 selected-dimension import requires unselected | TRACK | |
| #772 Python dup detector parses string fixtures | DONE | AST-gated extraction |
| #771 selftest suites treated as untested | DONE | *_selftest zone + naming convention |
| #770/#769 Python orphan misses nested pkg/__main__ CLIs | DONE | source_dir roots + __main__ guard hook |
| #761 TS body extraction stops in typed params | DONE | signature-brace tracking (ported #721, d5b770e5) |
| #759 scan output/history disagree after FP adjudication | TRACK | |
| #758 in-file selftests reported untested | DONE | has_inline_tests: selftest fn + __main__/argv wiring |
| #756 Rust orphan flags custom cargo bin target | DONE | _cargo_target_paths entry roots |
| #755 Codex ENRICH nested subagents | SKIP | runner prompt |
| #754 triage ORGANIZE contradicts requirements | TRACK | |
| #748 relative exclusions → Bandit keeps out-of-scope | DONE | same fix family as #916 |
| #746 Python src-layout imports orphaned at root scan | DONE | src/ resolution root |
| #728 bandit not registered under [full] extras | DONE | module-importable bandit check (ported #762) |
| #727 auto-detect cxx over csharp via ignores | DONE | exclusion-aware fallback count + sln/slnx/csproj/fsproj/Directory.Packages.props markers |
| #726/#683 C# namespace co-membership as import edge | DONE | co-membership via identifiers (#890) + FQ-ref edges |
| #717/#716/#714 Windows decoding/executable/npx | SKIP | Windows |
| #715 tree-sitter dep graph drops relative + CJS edges | DONE | ported #874+#920 — canonical compare + require() query |
| #709 next_lint removed in Next.js 16 | DONE | cmd_resolver → eslint direct on next>=16 (d8267ca0) |
| #705 tsconfig paths aliases unresolved → orphan FPs | DONE | ported #924+#925 (36dfaf86, 324811f2) |
| #701 plan resolve auto-completes unrelated steps | DONE | same root as #931 (6871a47e) |
| #700 Swift Xcode misdetected as TS | DONE | b71152c1 — zero-reviewable-file policy: loud warn + no subjective queue |
| #678 Django live modules reported dead | DONE | framework conventions |
| #675 cluster --depends-on replaces not appends | DONE | append+dedupe (ports PR #708) |
| #674 plan skip exits 0 on zero-match | DONE | CommandError exit 1 on skip/unskip/backlog (ports PR #706) |
| #665 importer_count misses @/ aliases | DONE | ported #924+#925 — per-importer tsconfig |
| #664 Python scan parses excluded virtualenv in coupling | DONE | same fix as #915 — exclusion-aware finder |
| #643 Go flat-dir counts _test.go as production | DONE | flat_dirs_filter excludes *_test.go |
| #642 Go coverage misses same-package behavior tests | DONE | already fixed — map_test_to_sources (3bac86a3) |
| #641 Go signature-variance conflates receiver types | DONE | methods extract as pkg.Recv.Name |
| #640 Go unused-import assumes last path segment | DONE | ported upstream PR #703 (fix a) |
| #563 (closed) mid-cycle scan blocked behind attest ceremony | DONE | `scan --rescan` added (fix f) |
| #544 (closed) hardcoded_secret_name ignores value | DONE | value-based gate (fix b) |
| #491 (closed) anti-gaming resets legitimate target scores | DONE | policy already disabled here; threats removed (fix e) |
| #254 (closed) lost updates on concurrent state mutation | DONE | scan merge now runs under `state_lock` (fix d) |

## Pull requests

| PR | Verdict | Note |
|---|---|---|
| #938 require detector evidence for manual scan verification | DONE | 243638ba — upstream PR port |
| #937 attribute strategist work to scored dimensions | DONE | 984a26dc — upstream PR port |
| #935 enforce trusted review coverage | DONE | fa91641c — upstream PR port |
| #926 Next.js entrypoints in nested packages | DONE | |
| #925/#924 TS aliases against each importer tsconfig | DONE | 36dfaf86 + 324811f2 |
| #920 JS import edges across scan root | DONE | |
| #914 keep excluded/git-ignored paths out of findings | DONE | high-value FP fix |
| #913/#912 Kotlin unused imports / import graph | SKIP | kotlin not exercised |
| #911 generic autofix tools per file | DONE | |
| #910 cxx C/C++ compilation languages in AST | DONE | |
| #904 absolute paths from collect_exclude_dirs | DONE | |
| #902 adopt Apache-2.0 | SKIP | relicensing is upstream's call; fork keeps OSNL |
| #901 cxx response-file/transitive header includes | DONE | |
| #899 cxx false API matches + security fallback | DONE | |
| #897 resolve relative scan roots before tool exclusions | DONE | pairs with #904 |
| #891 shared queue context review targets | DONE | d89f3562 — upstream PR port |
| #890 C# precise deps + iterator control flow | DONE | |
| #889 external scanner exclusions → absolute paths | DONE | same family as #897 |
| #881 review freshness + queue prerequisites | DONE | upstream PR port — canonical FP-only freshness suppression, pre-save plan reconcile, FP-only plan reconstruction restore |
| #880 unchanged scan corroboration invalidating reviews | DONE | 5358e946 — upstream PR port |
| #879 persist strategy work-item resolution | DONE | adbe6c96 — upstream PR port + queue-purge completion |
| #878 Dart signature analysis | SKIP | dart |
| #877 plan override IDs one canonical batch | DONE | 9beefa13 — upstream PR port |
| #876 Dart import semantics | SKIP | |
| #875 ignore overlapping spans in duplicate matching | DONE | dupes |
| #874 JS dep edges for relative paths + CommonJS | DONE | overlaps #920 — take one |
| #870 completed findings preserved on cluster defer | DONE | d42ec911 — upstream PR port |
| #869 C++ unused-function across batches | DONE | |
| #868 nonzero status for invalid show usage | DONE | trivial CLI correctness |
| #865 cxx Unreal automation tests | SKIP | Unreal |
| #864 cxx header dialect + cppcheck limits | DONE | |
| #862/#861 cxx header deps / TUs as build roots | DONE | |
| #860 cxx security findings from parser diagnostics | DONE | |
| #857 preserve scan scope through review imports | DONE | 15fc5571 — upstream PR port |
| #852 ignore future-only Python facade imports | DONE | |
| #851 configured target in review preflight | DONE | 951f6224 — upstream PR port |
| #850 consolidated triage organize steps | DONE | 11ead1cd — upstream PR port |
| #848 filtered empty views vs completed queues | DONE | 3954eb8b — upstream PR port |
| #844 scan isolation + review workflow consistency | DONE | ecaebee7 — state_lock merge + preflight config propagation |
| #841 frozen review scope in triage collection | DONE | c6939cac — upstream PR port + empty-frozen coverage fix |
| #840 fully covered selected-dimension reviews | DONE | 7eefcfd2 — upstream PR port |
| #837 review state + detector verification scope | DONE | upstream PR #837 port |
| #836 deliberate skip dispositions across scans | DONE | da6ce101 — upstream PR #836 port |
| #835 queue targets + scope plans to state files | DONE | upstream PR #835 port |
| #802 exact issue ID precedence over prefix | DONE | |
| #762 config excludes in bandit + module-installed bandit | DONE | |
| #750 count CommonJS require() as import edge | DONE | superseded by ported #874+#920 |
| #744 integrate 27 reviewed PRs | TRACK | meta-PR — mine for port candidates |
| #741 rust member/nested-worktree boundaries | DONE | |
| #740 Kotlin operator convention imports | SKIP | |
| #739 JVM imports in Gradle/Maven roots | DONE | |
| #738 opencode batch payload fences | SKIP | runner |
| #737 opencode via shutil.which on Windows | SKIP | |
| #735 C# reachable code flagged unreachable | DONE | |
| #734 Luau plugin | SKIP | new language, not a fix |
| #731 gdscript class_name/scene refs | SKIP | |
| #723 cxx cppcheck include-path harvesting | DONE | |
| #722 bound Rust coverage dep resolution | DONE | |
| #721 harden TS scanning + plan resolution | DONE | |
| #713 harden TS project/async detection | DONE | |
| #712 scale+correct Rust coverage mapping | DONE | |
| #710 java PMD -f text | DONE | |
| #703 Go import identifiers from package not path | DONE | ported (fix a) |
| #699 bash sourced library usage in unused-import | DONE | |
| #686 preserve queue and triage scopes | TRACK | |
| #658/#650 triage execution handoff | TRACK | |
| #633 Go package-level test coverage credit | DONE | |
| #620 bandit config-level excludes | DONE | overlaps #762 |

## Ported in this fork (done)

| Item | Commit |
|---|---|
| #703 / #640 Go unused-import package identifier | `9b0d1544` |
| Value-based `hardcoded_secret_name` detection (#544, #842, #885 class) | `8675f9cf` |
| Sanitizer-aware `dangerouslySetInnerHTML` / `.innerHTML` | `e75c9473` |
| Concurrent scan state races via `state_lock` merge (#254 class) | `993f1f53` |
| Remove stale anti-gaming reset threats (#923); document attested-import requirements | `72ff47d3` |
| `scan --rescan` sanctioned mid-cycle rescan (#563, #787, #856 class) | `92948def` |
| `scan --path` default falls back to `.` when `src/` absent (#934 class) | `ca27da49` |
| `scan --diff` PR review mode + `action.yml` + example workflow | `e2753807` |
| #723 cxx cppcheck include-path harvesting | `2206a2ee` |
| #862/#861 cxx header deps / TUs as build roots | `0b89c69a` |
| #869 cxx unused-function across batches | `34dd8ace` |
| #899 cxx false API matches + security fallback | `89702e62` |
| #901 cxx response-file + transitive header includes | `61bd10f3` |
| #910 cxx compilation languages in AST analysis | `9a27b838` |
| #924 TS aliases resolved against each importer tsconfig | `36dfaf86` |
| #925 TS coverage aliases from importer tsconfig | `324811f2` |
| #838 props detector counts only member lines | `60c61251` |
| #811 sort_no_comparator skips string-keyed Object sources | `d1205d5c` |
| #927 move preserves explicit TS extensions / index forms | `e4fd165a` |

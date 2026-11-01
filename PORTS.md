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
| #934 review defaults to missing src when scan_path null | PORT | same root as our (g): default path resolution |
| #933 TS coverage/dep resolvers miss workspace exports | PORT | monorepo correctness |
| #932 next recommends dead-useeffect autofix for README finding | SKIP | nudge wording |
| #931 queued work auto-completes unrelated steps | TRACK | queue machinery |
| #930 plan cluster add crashes on protected skip | TRACK | |
| #929/#928 backlog duplicate IDs / repeats findings | TRACK | |
| #927 move misses imports with explicit TS extensions | PORT | move correctness |
| #923 CLI threatens target-match resets though policy disabled | DONE | fixed here — threat text aligned with disabled policy (fix e) |
| #922 plan resolve exits 0 on queue-order guard reject | TRACK | |
| #921 test-coverage summary labels LOC potential wrong | SKIP | display |
| #919 cluster resolve rejects cluster shown by next | TRACK | |
| #918/#917 Windows triage UTF-8 / npm codex.cmd quoting | SKIP | Windows runner |
| #916 relative scan roots → relative Bandit exclusions | PORT | exclusion correctness (has PR #897/#914) |
| #915 Python dynamic import discovery ignores exclusions | PORT | |
| #909 Windows JS dep graph zero import edges | SKIP | Windows tree-sitter |
| #908 blind review prompts leak prior subjective scores | TRACK | review pipeline |
| #907 Python external-test mapping loses import roots | PORT | coverage mapping |
| #906 skipped assessments select empty next queue | TRACK | |
| #905 Python coverage misses importlib hyphenated CLIs | PORT | |
| #903 C++ signature variance false compares | PORT | cxx detector |
| #900 strategist history schema drift | TRACK | |
| #898 cluster-name resolution vs member IDs | TRACK | |
| #894 (closed) scan reopens adjudicated findings | DONE upstream | |
| #893 C# inferred property receivers → transitive_only | PORT | csharp detector |
| #892 C# custom test runners → no_tests | PORT | |
| #888 triage step-count / queue deadlock | TRACK | |
| #887 Go scanner invokes removed golangci-lint v1 flag | PORT | Go toolchain drift — check `golangci-lint run --out-format` compat |
| #886 Windows Codex batch quoting/locale | SKIP | |
| #885 C# field names flagged as secrets | DONE (class) | covered by value-based secret gate (fix b) |
| #884 clarify defer disposition in triage prompts | TRACK | prompt copy |
| #883 strategist recent_investment counts lifetime | TRACK | |
| #882 repeated strategist identifiers erase evidence | TRACK | |
| #873 duplicate detector compares nested callbacks to container | PORT | dupes detector |
| #872 accepting unchanged findings schedules another review | TRACK | |
| #867 cppcheck batching → cross-batch unused FPs | PORT | cxx |
| #866 C++ test import mapping behind headers | PORT | |
| #863 strict score penalizes auto_resolved | TRACK | scoring semantics |
| #859 C++ orphan detector misclassifies Unreal modules | SKIP | Unreal-specific |
| #858 TS coverage transitive_only for rendered components | PORT | |
| #856 codex --scan-after-import blocked by new queue | DONE (class) | `--rescan` is the sanctioned bypass (fix f) |
| #855 plan skip restoration leaves stale reopened metadata | TRACK | |
| #854 lru_cache_mutable flags immutable ctor globals | PORT | python detector |
| #853 Python unused detector silent zero without Ruff | PORT | tool-missing surfacing |
| #849 Python orphan misses Alembic runtime modules | PORT | |
| #847 mixin contract misses inherited methods | PORT | |
| #846/#801 dict_keys FPs for fallbacks/aliases | PORT | python detector |
| #845 observe triage: holistic issues can't be cited by hash | TRACK | |
| #842 RequestInit credentials flagged as secret | DONE (class) | value-based gate (fix b) — `credentials: "include"` has no secret value |
| #838 TS props detector counts union alternatives | PORT | |
| #832 next/plan ignore plan dir implied by --state | TRACK | |
| #831 TS unused ignores tsconfig.json | PORT | |
| #830 partial trusted review import resolves outside dimension | TRACK | |
| #829 schema-drift clustering quadratic | SKIP | perf |
| #827 CLI commit records omit cluster attribution | TRACK | |
| #826 blind packet structure profiles go stale | TRACK | |
| #825 triage includes inactive historical clusters | TRACK | |
| #824 Rust multiline attributes hide annotations | PORT | rust |
| #823 triage runner loses language/state in mixed projects | TRACK | |
| #821 boilerplate detector drops scoring potential | TRACK | |
| #815 mixed-language review imports remove queue items | TRACK | |
| #814 Python coverage misses runpy.run_path tests | PORT | |
| #813 post-flight refresh in queue but next empty | TRACK | |
| #811 sort_no_comparator warns on canonical ordering | PORT | ts-smells |
| #810 TS async_no_await mistakes return types for bodies | PORT | |
| #809 review imports scan-verify + stale fresh assessments | TRACK | |
| #808 PyPI 1.0 locale-dependent Codex decoding | SKIP | Windows |
| #807 scan prints conflicting pre/live scores | SKIP | output |
| #806 multi-file ShellCheck can crash silently | PORT | bash |
| #805 targeted re-review requires unselected dims | TRACK | |
| #787 recovered queue item requests scan the guard rejects | DONE (class) | `--rescan` (fix f) |
| #786 security detector FPs for static logs/JSON parsing | PORT | security filters |
| #785 scan persists to wrong language state on exclusion change | TRACK | |
| #784 reflect permits defer but validation rejects it | TRACK | |
| #780 next --state loads wrong plan | TRACK | |
| #779/#779 selected-dimension import requires unselected | TRACK | |
| #772 Python dup detector parses string fixtures | PORT | |
| #771 selftest suites treated as untested | PORT | |
| #770/#769 Python orphan misses nested pkg/__main__ CLIs | PORT | |
| #761 TS body extraction stops in typed params | PORT | |
| #759 scan output/history disagree after FP adjudication | TRACK | |
| #758 in-file selftests reported untested | PORT | |
| #756 Rust orphan flags custom cargo bin target | PORT | |
| #755 Codex ENRICH nested subagents | SKIP | runner prompt |
| #754 triage ORGANIZE contradicts requirements | TRACK | |
| #748 relative exclusions → Bandit keeps out-of-scope | PORT | same fix family as #916 |
| #746 Python src-layout imports orphaned at root scan | PORT | |
| #728 bandit not registered under [full] extras | PORT | packaging |
| #727 auto-detect cxx over csharp via ignores | TRACK | detection |
| #726/#683 C# namespace co-membership as import edge | PORT | csharp graph |
| #717/#716/#714 Windows decoding/executable/npx | SKIP | Windows |
| #715 tree-sitter dep graph drops relative + CJS edges | PORT | js graph (has PR #874/#920) |
| #709 next_lint removed in Next.js 16 | PORT | tool compat |
| #705 tsconfig paths aliases unresolved → orphan FPs | PORT | (has PR #924/#925) |
| #701 plan resolve auto-completes unrelated steps | TRACK | |
| #700 Swift Xcode misdetected as TS | TRACK | detection |
| #678 Django live modules reported dead | PORT | python orphan |
| #675 cluster --depends-on replaces not appends | TRACK | (closed PR #708 exists) |
| #674 plan skip exits 0 on zero-match | TRACK | (closed PR #706 exists) |
| #665 importer_count misses @/ aliases | PORT | |
| #664 Python scan parses excluded virtualenv in coupling | PORT | |
| #643 Go flat-dir counts _test.go as production | PORT | go detector |
| #642 Go coverage misses same-package behavior tests | PORT | |
| #641 Go signature-variance conflates receiver types | PORT | |
| #640 Go unused-import assumes last path segment | DONE | ported upstream PR #703 (fix a) |
| #563 (closed) mid-cycle scan blocked behind attest ceremony | DONE | `scan --rescan` added (fix f) |
| #544 (closed) hardcoded_secret_name ignores value | DONE | value-based gate (fix b) |
| #491 (closed) anti-gaming resets legitimate target scores | DONE | policy already disabled here; threats removed (fix e) |
| #254 (closed) lost updates on concurrent state mutation | DONE | scan merge now runs under `state_lock` (fix d) |

## Pull requests

| PR | Verdict | Note |
|---|---|---|
| #938 require detector evidence for manual scan verification | TRACK | verification flow |
| #937 attribute strategist work to scored dimensions | TRACK | |
| #935 enforce trusted review coverage | TRACK | |
| #926 Next.js entrypoints in nested packages | PENDING | |
| #925/#924 TS aliases against each importer tsconfig | PORT | |
| #920 JS import edges across scan root | DONE | |
| #914 keep excluded/git-ignored paths out of findings | DONE | high-value FP fix |
| #913/#912 Kotlin unused imports / import graph | SKIP | kotlin not exercised |
| #911 generic autofix tools per file | DONE | |
| #910 cxx C/C++ compilation languages in AST | PENDING | |
| #904 absolute paths from collect_exclude_dirs | DONE | |
| #902 adopt Apache-2.0 | SKIP | relicensing is upstream's call; fork keeps OSNL |
| #901 cxx response-file/transitive header includes | PENDING | |
| #899 cxx false API matches + security fallback | PENDING | |
| #897 resolve relative scan roots before tool exclusions | DONE | pairs with #904 |
| #891 shared queue context review targets | TRACK | |
| #890 C# precise deps + iterator control flow | DONE | |
| #889 external scanner exclusions → absolute paths | DONE | same family as #897 |
| #881 review freshness + queue prerequisites | TRACK | |
| #880 unchanged scan corroboration invalidating reviews | TRACK | |
| #879 persist strategy work-item resolution | TRACK | |
| #878 Dart signature analysis | SKIP | dart |
| #877 plan override IDs one canonical batch | TRACK | |
| #876 Dart import semantics | SKIP | |
| #875 ignore overlapping spans in duplicate matching | DONE | dupes |
| #874 JS dep edges for relative paths + CommonJS | DONE | overlaps #920 — take one |
| #870 completed findings preserved on cluster defer | TRACK | |
| #869 C++ unused-function across batches | PENDING | |
| #868 nonzero status for invalid show usage | DONE | trivial CLI correctness |
| #865 cxx Unreal automation tests | SKIP | Unreal |
| #864 cxx header dialect + cppcheck limits | DONE | |
| #862/#861 cxx header deps / TUs as build roots | PORT | |
| #860 cxx security findings from parser diagnostics | DONE | |
| #857 preserve scan scope through review imports | TRACK | |
| #852 ignore future-only Python facade imports | DONE | |
| #851 configured target in review preflight | TRACK | |
| #850 consolidated triage organize steps | TRACK | |
| #848 filtered empty views vs completed queues | TRACK | |
| #844 scan isolation + review workflow consistency | TRACK | umbrella — review before porting |
| #841 frozen review scope in triage collection | TRACK | |
| #840 fully covered selected-dimension reviews | TRACK | |
| #837 review state + detector verification scope | TRACK | |
| #836 deliberate skip dispositions across scans | TRACK | |
| #835 queue targets + scope plans to state files | TRACK | |
| #802 exact issue ID precedence over prefix | DONE | |
| #762 config excludes in bandit + module-installed bandit | DONE | |
| #750 count CommonJS require() as import edge | DONE | superseded by ported #874+#920 |
| #744 integrate 27 reviewed PRs | TRACK | meta-PR — mine for port candidates |
| #741 rust member/nested-worktree boundaries | DONE | |
| #740 Kotlin operator convention imports | SKIP | |
| #739 JVM imports in Gradle/Maven roots | DONE | |
| #738 opencode batch payload fences | SKIP | runner |
| #737 opencode via shutil.which on Windows | SKIP | |
| #735 C# reachable code flagged unreachable | PENDING | |
| #734 Luau plugin | SKIP | new language, not a fix |
| #731 gdscript class_name/scene refs | SKIP | |
| #723 cxx cppcheck include-path harvesting | PENDING | |
| #722 bound Rust coverage dep resolution | PENDING | |
| #721 harden TS scanning + plan resolution | PENDING | |
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

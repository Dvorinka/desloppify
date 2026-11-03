# Changelog

## [1.0.1] — community fork, `maint/continuation` (unreleased)

Community continuation of `peteromallet/desloppify` at v1.0 (`3a7735d`).
Maintained at [Dvorinka/desloppify](https://github.com/Dvorinka/desloppify).
Upstream issue/PR triage lives in [PORTS.md](PORTS.md).

### Added

- `scan --rescan` — sanctioned mid-cycle rescan. Refreshes findings while
  preserving issue IDs, queue state, and the plan baseline; no `--attest`
  ceremony (upstream #563; unblocks #787/#856-class flows).
- `scan --diff <base>` — PR review mode. Maps open findings onto
  `base...HEAD` changed lines, prints annotations plus the strict-score
  delta, emits GitHub Actions `::warning` commands, and supports
  `--annotations-json <path>` for CI consumers. Mechanical only, no LLM.
- `action.yml` + `examples/pr-review.yml` — reusable composite action and
  example workflow for desloppify-as-PR-reviewer.
- `review --run-batches --batch-mode {per-dimension,grouped,single}` —
  subagent review cost control. Default `per-dimension` runs one agent per
  dimension (~20 runs); `grouped` merges dimensions sharing a holistic
  evidence collector (~9 runs); `single` runs all dimensions in one agent
  (cheapest, shallowest). `run_summary.json` records the mode so
  `--import-run` replays the same grouping.

### Fixed

- Plan/queue machinery (upstream #906, #919, #928/#929, #930, #931/#701):
  skipped assessments no longer select a postflight phase that then empties
  the queue; the resolve queue-order guard mirrors `next`'s cluster-focus
  view; `backlog` dedupes canonical IDs that surfaced in multiple
  partitions; `plan cluster add` refuses skipped IDs instead of crashing in
  validation; `auto_complete_steps` only completes a step when its
  referenced findings are absent from the plan AND not still open in state.
- `next --state`/`backlog --state` now load the sibling plan for the given
  state path instead of the default project plan (upstream #780).
- Go `unused` detector no longer assumes the last import-path segment is the
  package identifier — versioned modules (`.../v8`), `gopkg.in` paths
  (`yaml.v3`), blank and dot imports handled; undeterminable names no longer
  flagged (ports upstream PR #703 / issue #640).
- `hardcoded_secret_name` is now value-gated: known secret formats always
  fire, everything else must clear a 12-char + 3.0 bits/char entropy bar, and
  identifier-shaped constants (`"clientSecret"`, `"token_usage"`) and
  translation strings are skipped (upstream #544, #842, #885 class).
- `dangerouslySetInnerHTML` / `.innerHTML` security checks skip comment
  lines, sanitizer-wrapped operands (DOMPurify etc.), quoted literals without
  interpolation, in-file static markup constants, and `''` clears.
- Scan state merge now runs under `state_lock`: state is reloaded under the
  lock, merged, and saved — concurrent commands and parallel scans on the
  same `state-<lang>.json` can no longer clobber each other (upstream #254
  class).
- Review importer and scan reporter no longer threaten target-match score
  resets the disabled anti-gaming policy cannot perform — they honor
  `subjective_integrity.status == "disabled"` (upstream #923).
- `scan --path` auto-detect falls back to the project root when `src/` is
  absent instead of producing a dead path (upstream #934 class).
- cxx cppcheck phase now passes `-I` dirs harvested from header parents and
  `compile_commands.json`, runs with `--check-level=exhaustive
  --inline-suppr`, and drops header "is never used" noise (upstream PR #723).
- cxx `unusedFunction` findings are verified by a whole-program cppcheck
  pass over a generated compilation database — batch-local claims alone no
  longer produce findings (upstream PR #869).
- cxx dependency graph follows transitive header includes per include
  context, expands `@file` response arguments, resolves entry `directory`
  relative to the database, and marks compiled translation units as entry
  points (upstream PRs #862, #901, #910).
- cxx tree-sitter analysis selects the C grammar for `.c` files and C++ for
  the rest; compilation-database loading is shared via
  `cxx/compile_commands.py` (upstream PR #910).
- cxx security scan treats cppcheck configuration/parse failures (missing
  includes, unknown macros, headers parsed as C) as reduced coverage and
  falls back to regex checks; unsafe-API names require identifier
  boundaries (upstream PR #899).
- Python `unused` detector reports reduced coverage when neither ruff nor
  pyflakes can run, instead of a silent zero (upstream #853).
- `lru_cache_mutable` no longer flags immutable constructor-backed globals
  (`re.compile`, `frozenset`, `tuple`, `MappingProxyType` over a fresh
  immutable literal) (upstream #854).
- Python import resolution covers nested packages under script dirs and
  src-layout roots; `__main__`-guarded files count as entry points; Django
  and Alembic runtime modules are recognized as framework-loaded; dynamic
  import discovery honors exclusions (upstream #770, #769, #746, #678,
  #849, #915, #664).
- Python function extraction ignores `def`s inside string fixtures — the
  AST gates which `def` tokens are real (upstream #772).
- Implicit mixin contract detector resolves `self.<method>()` through own
  and inherited methods instead of reporting them as undeclared host
  attributes (upstream #847).
- TypeScript coverage resolver now shares the dep graph's candidate
  enumeration: NodeNext `./x.js` specifiers resolve to `.ts`/`.tsx`
  sources, and `~/` joins `@/` in the tsconfig-paths fallback
  (declared mappings win) — direct imports that both resolvers missed
  no longer report transitive_only/untested (upstream #858).
- Python coverage maps scan-root-relative imports from tests outside the
  scanned root (unambiguous suffix match), `importlib` file-load paths
  (`spec_from_file_location`, `SourceFileLoader`, `imp.load_source`)
  count as test imports, `*_selftest.py` files classify as tests with an
  `X_selftest.py -> X.py` naming convention, and executable in-file
  `--selftest` entry points count as coverage when wired to `__main__`
  (upstream #907, #905, #771, #758).
- Coverage graph/path normalization unifies `\\` to `/` so Windows
  graph keys match zone paths; the coverage phase labels its
  sqrt(LOC)-weighted potential honestly (upstream #907).
- Python `dict_keys` no longer flags `self.x` dicts consumed by sibling
  methods, dicts that escaped through call boundaries or were rebound to
  unseen content (phantom reads), conditional/branch writes (sequential
  overwrite claims now require two unconditional writes), or dicts moved
  through for-iter container aliases (upstream #801, #846).
- Review freshness + queue-tracking family (upstream PRs #881, #877, #850,
  #848, #870, #835/#836, #837, #840, #841, #857, #852, #851, #879; issues
  #832, #830, #826, #825, #823, #821, #815, #813, #809, #805, #785, #779,
  #759, #754, #908): canonical false-positive-only skip freshness with the
  raw merge saved under `state_lock` before reconciliation; a reduced
  jscpd run lowers coverage instead of silently keeping full weight;
  per-language `--state` files isolated plan queues (`plan_path_for_state`);
  partial trusted imports bounded by packet-declared dimensions;
  `review --prepare` refreshes the blind packet; `show --blind` suppresses
  the plan/score footers; triage helper bakes `--lang`/`--state` into the
  script; scan history scores are rewritten in-lock so output, history,
  and disk agree; organize refusals exit 1; strategy items resolve through
  the canonical state path and survive force-rescan (upstream #900/#888
  family: `strategy::` ids execute through `next`, phase markers split
  from persisted work, execution logs separate operations from issue ids).
- Detector/resolver family (upstream PRs #938, #935, #937, #925/#924,
  #920, #914, #926, #911, #874, #910, #901; issues #927, #933, #831, #838,
  #811, #810, #824, #854, #887, #709, #727, #700, #863): detector-evidence
  gates for manual scan verification, packet-scoped trusted-review
  coverage, tsconfig-alias resolution per importer, JS/CJS import edges,
  git-ignored paths dropped from findings, Next.js nested-package
  entrypoints, generic autofix per-file protocol, golangci v2 flag
  detection, Swift `Tests/` zone rules, jscpd run from a neutral cwd.
- Upstream meta-PR #744 fully mined: ports from it include the cxx regex
  atomic groups (#729/#733), bandit discovered-file batches (#695),
  schema-correction contexts (#694), pure-forwarding AST shapes (#693),
  versioned-migration constants (#691), compat import entry points (#690),
  constant-return CLI main (#688), callable-default None providers (#687),
  open dict-copy keysets (#673), reflect display names (#685),
  Razor/Blazor dep-graph links (#682), React Router/Remix route modules
  (#697), tested-header same-stem mapping (#732).
- TypeScript cyclomatic complexity no longer charges nested function and
  arrow bodies to the enclosing function; complex callbacks are still
  flagged on themselves (upstream #839).
- Python `unused_enums` treats same-module value and annotation uses as
  live consumers; self-references inside the enum body do not count
  (upstream #843).

### Changed

- README/docs repointed to the fork; install via
  `pip install "desloppify[full] @ git+https://github.com/Dvorinka/desloppify"`.
- SKILL.md documents the triage report contract (literal issue IDs,
  `## Coverage Ledger`) and `--attested-external` requirements.

## PR review mode (W2)
- `scan --diff BASE` was already bundled: mechanical annotations on
  `BASE...HEAD` changed lines + strict-score delta. New this arc:
  `--max-regression POINTS` gates the run (exit 3) when the strict score
  drops more than allowed vs the stored baseline.
- Root `action.yml` gained a `fail-on-regression` input wired to
  `--max-regression`; `Dvorinka/desloppify@main` usable as a PR check.
- `.github/workflows/desloppify-pr-review.example.yml` — copy-paste
  consumer workflow (checkout fetch-depth 0 + action + gate example).

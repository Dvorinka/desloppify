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

### Fixed

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

### Changed

- README/docs repointed to the fork; install via
  `pip install "desloppify[full] @ git+https://github.com/Dvorinka/desloppify"`.
- SKILL.md documents the triage report contract (literal issue IDs,
  `## Coverage Ledger`) and `--attested-external` requirements.

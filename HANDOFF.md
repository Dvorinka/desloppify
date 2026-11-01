# Handoff — desloppify community fork continuation

## State
- Repo: `~/Desktop/PROG+HTML/desloppify`, branch `maint/continuation`, pushed to
  `Dvorinka/desloppify`. Summary PR #1 open (do not merge yet).
- Test env: `.venv` at repo root (`pip install -e ".[treesitter]" pytest`).
  Tree-sitter extras REQUIRED — many detector tests pass trivially without them.
- PORTS.md = triage ledger. CHANGELOG.md = delta vs upstream v1.0 (3a7735d).

## Immediate next work (in order)
1. **cxx-family merges (6 PENDING)**: upstream PRs #723, #862, #869, #899, #901, #910.
   All conflict under `git apply --3way` in `desloppify/languages/cxx/{detectors/deps.py,
   phases.py, detectors/security.py}` + their tests. Diffs cached locally? Re-fetch:
   `gh pr diff <n> -R peteromallet/desloppify > /tmp/pr<n>.diff`. Merge strategy that
   worked: apply --3way, inspect `<<<<<<< ours`/`=======`/`>>>>>>> theirs`, prefer
   "theirs" when it's a superset fix, keep BOTH sides for adjacent test additions,
   then run the PR's touched test files. Watch for dropped bindings (a #721 merge
   needed `project_root` reinstated).
2. **PORT-verdict items without PRs** (49 rows): real bugs needing original fixes —
   mostly detector FPs in Rust/C++/C#/JVM/Python/TS. Each = own commit + test.
3. **TRACK (61)**: deep queue/plan machinery bugs — do after detectors settle.
4. **New features queue**: more `--diff` polish (per-line severity levels, SARIF
   output for code-scanning upload), `--rescan` docs, maybe `desloppify review-diff`
   alias if users want it named.

## Learned pitfalls
- `desloppify/data/global/SKILL.md` must equal `docs/SKILL.md` (bundled-sync test).
- `save_state` recomputes scores — stamp `strict_score` etc. by patching JSON directly.
- `load_state` reconstructs from plan.json when scan_source != "scan" — set `last_scan`.
- CLI flag order: `desloppify --lang X scan ...` (global flag, not subcommand flag).
- Commits need `Authored By: TDvorak <info@tdvorak.dev>` trailer.

## Verified on Invico
`desloppify --lang typescript scan --path apps/web --profile ci --no-badge` works —
reads upstream-written `.desloppify` state fine, preserved plan/baseline, scores.

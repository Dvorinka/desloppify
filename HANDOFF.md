# Handoff — desloppify community fork continuation

## State
- Repo: `~/Desktop/PROG+HTML/desloppify`, branch `maint/continuation`, pushed to
  `Dvorinka/desloppify`. Summary PR #1 open (do not merge yet).
- Test env: `.venv` at repo root (`pip install -e ".[treesitter]" pytest`).
  Tree-sitter extras REQUIRED — many detector tests pass trivially without them.
- PORTS.md = triage ledger. CHANGELOG.md = delta vs upstream v1.0 (3a7735d).

## Immediate next work (in order)
1. ~~cxx-family merges~~ DONE — #723/#862/#869/#899/#901/#910 hand-merged.
   Notable resolution choices: deps.py keeps the #862 `expanded`/`include_specs`
   traversal over #901's `visited_by_context`; `_expand_response_tokens` moved
   into `cxx/compile_commands.py` under #910's shared loader; cppcheck prefix
   keeps the `{id}` template field (analysis-notice classification needs it).
2. **PORT-verdict items** (~32 rows left in PORTS.md): Python detector +
   orphan/exclusion families done (#853/#854/#847/#770/#769/#746/#678/#849/
   #915/#664/#772; #771 partially — `*_selftest` coverage mapping still open).
   Remaining bulk: TS/JS (#933/#927/#858/#838/#831/#811/#810/#761/#709/#705+
   #924/#925/#665), C# (#893/#892/#726/#683), Go (#887/#643/#642/#641),
   Rust (#824/#756), cxx (#903/#866), misc (#873/#806/#786, #907/#905,
   #846/#801 dict_keys, #814 runpy coverage).
   Fetch each issue body before fixing: `gh issue view N -R peteromallet/desloppify`.
3. **TRACK (61)**: deep queue/plan machinery bugs — untouched, do after detectors.
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

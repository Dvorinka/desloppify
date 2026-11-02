# Handoff prompt — paste into a fresh session

You are continuing a multi-repo maintenance sweep. Everything below is verified state; resume without re-surveying.

## Ground rules

- Fork repo: `/home/tdvorak/Desktop/PROG+HTML/desloppify`, branch `maint/continuation`, remote `https://github.com/Dvorinka/desloppify.git`. NEVER touch upstream `peteromallet/desloppify` — `gh issue/pr view -R peteromallet/desloppify` for reading only.
- Persistent memory: `git -C ~/agent-memory pull --ff-only`, read MEMORY.md, append durable facts, commit+push. Latest entry describes this sweep.
- Repo ledger: `PORTS.md` (issue status rows) + `HANDOFF.md` (session notes) — update on every resolved item.
- Commits: Conventional Commits, trailer `Authored By: TDvorak <info@tdvorak.dev>`. Push after each resolved item.
- Lint: `ruff check` (binary at `/home/tdvorak/.local/bin/ruff`; `.venv/bin/ruff` does NOT exist). Several files have PRE-EXISTING ruff I001/E402 noise (parser_groups.py, show/cmd.py, orchestrator_codex_pipeline.py) — verify with `git stash` + ruff before attributing to your diff; leave it.
- Tests: `.venv/bin/python -m pytest desloppify/tests -q`. Known environmental failures (ignore, don't chase): `TestCmdReviewPrepare::test_do_run_batches_dry_run_generates_packet_and_prompts` in both `tests/review/integration/test_review_commands.py` and `tests/review/test_review_commands.py`. Any OTHER failure is yours.
- Style: smallest correct diff, reuse existing helpers, regression test per fix. Follow existing commit style (`port: upstream PR #N — title` / `fix(scope): desc (#N)`).
- Several "queued" issues turn out already-fixed by earlier ports (#844, #835/#911 families) — verify code behavior FIRST, then write only the regression test. This session: #944, #832, #815 were already fixed; #943 was 90% fixed (one call site remained).

## Completed so far (all pushed through 50337388)

- Upstream PR sweep: COMPLETE (all ported or covered; #902 license skipped deliberately).
- New issues #944 #943 #942 #941 #940 #908 — all closed.
- TRACK backlog started: #832, #823, #821, #815 — all closed.
- Details in PORTS.md rows + HANDOFF.md Session XII entries.

## Remaining desloppify queue (in order)

1. **#809** — review imports scan-verify + stale fresh assessments (TRACK).
2. **#805** — targeted re-review requires unselected dims (TRACK).
3. **#785** — scan persists to wrong language state on exclusion change (TRACK).
4. **#779** — selected-dimension import requires unselected (TRACK, dup of #779/#779 row).
5. **#759** — scan output/history disagree after FP adjudication (TRACK).
6. **#754** — triage ORGANIZE contradicts requirements (TRACK).
7. Meta rows: **#686** (preserve queue and triage scopes), **#658/#650** (triage execution handoff), **#744** (meta-PR — mine for port candidates).
   Read PORTS.md notes per row before starting; re-fetch bodies via `gh issue view N -R peteromallet/desloppify`.

## Then: Dvorinka/cloudreve

- `gh issue list -R Dvorinka/cloudreve` — #412 (known vulns in 4.19.1 Docker image: Go toolchain, modules, Alpine packages — likely bump base image/deps), #369 (upstream watch meta issue — likely close or leave with comment).
- PRs #414 (Android: complete 2FA login flow + fix dark-mode login form, branch `fix/android-2fa-login`) and #413 (Android: don't attach auth token to presigned object-storage URLs). Review code, verify, merge or fix-then-merge per repo convention.

## Then: Dvorinka/Nothing_Modes (user-prescribed order — follow exactly)

1. **Crash fix first.** Two identical reports: `android.database.sqlite.SQLiteFullException: database or disk is full (code 13)` in Room `endTransaction` (obfuscated `d5.b.e`/`androidx.room.w.b`, `DefaultDispatcher-worker-4`), app 0.19.11, Infinix X6725. Likely unbounded Room writes (cache/history/log table) without disk-space handling — implement bounded retention/cleanup + graceful SQLITE_FULL degradation.
2. Add the fix to open **PR #42** (`feature/onboarding-guide` — onboarding guide, starter modes, Bluetooth control, reviewer fixes). Resolve review state and merge it per repo convention.
3. Run desloppify on the Nothing_Modes repo ONLY (install/run from the desloppify checkout).
4. Write ALL findings into a file in the Nothing_Modes workspace — do NOT fix any of them.
5. "Release the pr" — cut/merge the release per repo convention; link the PR URL.

## Mechanisms learned this session (reuse, don't rebuild)

- `runtime.plan_file` (RuntimeContext) + `plan_path_for_state(state_path)`: cli.py sets it from `--state`; `load_plan()`/`get_plan_file()` resolve through it. This is what isolates per-language execution queues (#832, #815).
- `read_coverage_file` (test_coverage/io.py) reads CWD-relative — tests must `monkeypatch.chdir(root)` or use absolute paths.
- `conftest.py` fixture `set_project_root` → RuntimeContext project_root for detector tests.
- `show --blind` flag exists now for score-free reviewer navigation.
- `make_generic_fixer` fixers declare `takes_scan_path`; every `fixer.fix()` call site must pass `path` under that flag (cmd.py + apply_retro cascade both do).
- `matched_ignore_pattern` retries `::` globs with implicit `::*` tail — `detector::*::rule` matches IDs with `::line` suffix.
- jscpd adapter: `_run_jscpd_command` takes `cwd=`; detect passes neutral output tmpdir.
- Failed-detector pattern: phase records reduced `DetectorCoverageStatus` via `_record_detector_coverage`, then `workflow._restore_failed_detector_potentials` preserves prior potential at merge.

## Notes

- `pull_request_linking`: after creating/taking over any PR, call `link_pull_request` with the full URL.
- `desloppify/data/global/SKILL.md` must equal `docs/SKILL.md` (bundled-sync test) — keep them in sync if either is edited.
- Upstream issue bodies are summarized in PORTS.md/HANDOFF.md; re-fetch via gh only if needed.

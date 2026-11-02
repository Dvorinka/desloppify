# Handoff prompt — paste into a fresh session

You are continuing a multi-repo maintenance sweep. Everything below is verified state; resume without re-surveying.

## Ground rules

- Fork repo: `/home/tdvorak/Desktop/PROG+HTML/desloppify`, branch `maint/continuation`, remote `https://github.com/Dvorinka/desloppify.git`. NEVER touch upstream `peteromallet/desloppify` — `gh issue/pr view -R peteromallet/desloppify` for reading only.
- Persistent memory: `git -C ~/agent-memory pull --ff-only`, read MEMORY.md, append durable facts, commit+push. Latest entry describes this sweep.
- Repo ledger: `PORTS.md` (issue status rows) + `HANDOFF.md` (session notes) — update on every resolved item.
- Commits: Conventional Commits, trailer `Authored By: TDvorak <info@tdvorak.dev>`. Push after each resolved item.
- Lint: `ruff check` (binary at `/home/tdvorak/.local/bin/ruff`; `.venv/bin/ruff` does NOT exist).
- Tests: `.venv/bin/python -m pytest desloppify/tests -q`. Known environmental failures (ignore, don't chase): `TestCmdReviewPrepare::test_do_run_batches_dry_run_generates_packet_and_prompts` in both `tests/review/integration/test_review_commands.py` and `tests/review/test_review_commands.py`. Any OTHER failure is yours.
- Style: smallest correct diff, reuse existing helpers, regression test per fix. Follow existing commit style (`port: upstream PR #N — title` / `fix(scope): desc (#N)`).

## Completed so far (all pushed through ~a10f89d3)

- Session X fixes: #888, #900, #825, #813, #830, #826 — see PORTS.md.
- Upstream PR sweep: COMPLETE. Ported #912+#939 (09556943), #913 (a10f89d3). Already ported earlier: #890 #897 #899 #901 #904 #910 #911 #914 #920 #924 #925 #926 #938. #902 (Apache relicensing) deliberately skipped — legal change, not mechanical.

## Remaining desloppify queue (in order)

1. **#944** — TS scans miss JS/.mjs tests incl root-level test dirs. `TypeScriptConfig.test_file_extensions` only `[".ts",".tsx"]`; `_find_external_test_files` skips test dirs at scan root. Extend coverage discovery to `.js/.jsx/.mjs/.cjs` tests for root AND subdir scans without widening production source scope. Symmetric fix exists in PR #783 for reference.
2. **#943** — generic autofix reports success without running formatter. `app/commands/autofix/cmd.py` calls `fixer.fix(entries, dry_run=dry_run)` without `path`; `make_generic_fixer` returns preview entries for `dry_run or not path`, counted as fixes. Must fail closed + pass scan root through a consistent fixer protocol; `apply_retro.py` has same omission. Also: dry-run prints findings as "files", infers fixed entries from count diff, drops scan excludes.
3. **#942** — Swift `Tests/<Target>Tests/` classified production (zone matcher case-sensitive, rules only `/tests/`). Add Swift-specific `Tests` rule rather than global case-folding.
4. **#941** — jscpd duplication detection dies on `EBADDEVENGINES` in pnpm-only devEngines workspaces. Run jscpd isolated from target workspace evaluation or honor configured package manager.
5. **#940** — two bugs: Lua `unused_import` flags string literals (load modes, `string.pack` formats, table keys) AND `detector::*::rule` suppress patterns can't match IDs with `::line` suffix (needs `::*` tail — fix matching or docs/UX).
6. **#908** — blind review prompts recommend `show` commands that expose prior subjective scores (TRACK in PORTS.md).
7. Backlog TRACK rows: `#832 #823 #821 #815 #809 #805 #785 #779 #759 #754`; meta rows `#686 #658/#650 #744`. Read PORTS.md notes per row before starting.

## Then: Dvorinka/cloudreve

- `gh issue list -R Dvorinka/cloudreve` — #412 (known vulns in 4.19.1 Docker image: Go toolchain, modules, Alpine packages — likely bump base image/deps), #369 (upstream watch meta issue — likely close or leave with comment).
- PRs #414 (Android: complete 2FA login flow + fix dark-mode login form, branch `fix/android-2fa-login`) and #413 (Android: don't attach auth token to presigned object-storage URLs). Review code, verify, merge or fix-then-merge per repo convention.

## Then: Dvorinka/Nothing_Modes (user-prescribed order — follow exactly)

1. **Crash fix first.** Two identical reports: `android.database.sqlite.SQLiteFullException: database or disk is full (code 13)` in Room `endTransaction` (obfuscated `d5.b.e`/`androidx.room.w.b`, `DefaultDispatcher-worker-4`), app 0.19.11, Infinix X6725. Likely unbounded Room writes (cache/history/log table) without disk-space handling — implement bounded retention/cleanup + graceful SQLITE_FULL degradation.
2. Add the fix to open **PR #42** (`feature/onboarding-guide` — onboarding guide, starter modes, Bluetooth control, reviewer fixes). Resolve review state and merge it per repo convention.
3. Run desloppify on the Nothing_Modes repo ONLY (install/run from the desloppify checkout).
4. Write ALL findings into a file in the Nothing_Modes workspace — do NOT fix any of them.
5. "Release the pr" — cut/merge the release per repo convention; link the PR URL.

## Notes

- `pull_request_linking`: after creating/taking over any PR, call `link_pull_request` with the full URL.
- Upstream issue bodies already summarized in HANDOFF.md; re-fetch via `gh issue view N -R peteromallet/desloppify` if needed.

You are continuing an autonomous multi-repo maintenance sweep overnight.
Run fully autonomous — do NOT stop for questions; make reasonable decisions
and record them in the ledgers.

STARTUP (read all of these first):
- /home/tdvorak/Desktop/PROG+HTML/desloppify/HANDOFF_PROMPT.md (original brief)
- /home/tdvorak/Desktop/PROG+HTML/desloppify/PORTS.md (issue/PR ledger)
- /home/tdvorak/Desktop/PROG+HTML/desloppify/HANDOFF.md (session notes)
- ~/agent-memory/MEMORY.md (after `git -C ~/agent-memory pull --ff-only`)

REPO: /home/tdvorak/Desktop/PROG+HTML/desloppify, branch maint/continuation,
remote github.com/Dvorinka/desloppify. NEVER touch upstream peteromallet —
read-only via `gh issue/pr view -R peteromallet/desloppify`.

DONE SO FAR (do not redo):
- Original queue fully closed: desloppify issues/TRACK rows, cloudreve
  (#412 closed, #369 commented, PRs #413+#414 merged), Nothing_Modes
  (SQLiteFullException fix → PR #42 merged → desloppify scan →
  .desloppify-findings.md → released v0.19.17).
- #744 mining: ported #729 #733 #695 #694 #693 #691 #690 #688 #687.

REMAINING WORK, in order:

1. Finish the #744 pending port candidates. For EACH of:
   py #673 (dict copy keysets), py #685 (reflect displayed dimension
   names), C# #682 (Razor/Blazor views in dep graph + extension-filter
   follow-up), TS #697 (React Router/Remix route modules as entry points),
   cxx #732 (static test coverage mapping — CLOSED unmerged upstream,
   port anyway if clean):
   a. `gh pr diff N -R peteromallet/desloppify` — review the full diff
      including tests.
   b. Check whether the fork already covers it (earlier ports overlap —
      verify behavior first; if covered, just note it).
   c. Port the source change, adapting to the fork's structure (the fork
      diverged: keep fork idioms like find_py_files exclusion-aware
      discovery).
   d. Port the upstream tests into the matching fork test file.
   e. Run: `.venv/bin/python -m pytest <targeted test files> -q` and
      `/home/tdvorak/.local/bin/ruff check <changed files>`.
   f. Update the #744 row in PORTS.md (move the candidate from "pending"
      to the ported list) and append a HANDOFF.md entry.
   g. Commit (Conventional Commits + `Authored By: TDvorak
      <info@tdvorak.dev>` trailer) and push.

2. Fresh upstream sweep for desloppify:
   `gh issue list -R peteromallet/desloppify --state open --limit 100`
   and `gh pr list -R peteromallet/desloppify --state open --limit 50`.
   Anything filed after the last sweep (issues > #944, PRs not in
   PORTS.md): triage each — verify applicability to the fork, port if
   relevant, or record SKIP/adjudication in PORTS.md + HANDOFF.md.
   Several upstream items may already be covered by earlier ports —
   verify before reimplementing; a regression test alone is fine.

3. Check open PRs across all three fork repos
   (`gh pr list -R Dvorinka/desloppify`, `-R Dvorinka/cloudreve`,
   `-R Dvorinka/Nothing_Modes`): review any open ones, fix if needed,
   merge per repo convention when checks pass (cloudreve+desloppify:
   squash; Nothing_Modes: merge commit + chore(release) bump +
   fastlane changelog + `gh release create vX.Y.Z --target main
   --generate-notes --latest`). If checks are still running when
   everything else is done, wait via watch_pull_request rather than
   sleeping; merge when green.

4. Close out:
   - Full desloppify suite once: `.venv/bin/python -m pytest
     desloppify/tests -q` — ignore ONLY the two
     test_do_run_batches_dry_run_generates_packet_and_prompts env
     failures. Any other failure must be fixed before finishing.
   - Update PORTS.md + HANDOFF.md with everything done this session.
   - Append a durable summary line to ~/agent-memory/MEMORY.md,
     commit and push the memory repo.
   - Leave the desloppify tree clean (git status empty).

CONVENTIONS: Conventional Commits + `Authored By: TDvorak
<info@tdvorak.dev>` trailer on every commit. Push after each resolved
item. Pre-existing ruff noise to leave: parser_groups.py, show/cmd.py,
orchestrator_codex_pipeline.py (I001/E402). Smallest correct diff;
reuse helpers; no speculative abstraction. J.A.R.V.I.S. style: concise,
dry, no emojis. Link any PR you create/take over via link_pull_request.

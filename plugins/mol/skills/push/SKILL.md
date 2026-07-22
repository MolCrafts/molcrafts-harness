---
name: push
description: Push current branch to origin (fork) after CI-parity pre-commit + /mol:ship push. Never pushes to upstream — land via /mol:pr. Auto-fix loop; never force-push. --no-verify only with explicit user consent. Auto-invoked by /mol:pr, /mol:release, /mol-plugin:release.
argument-hint: "[<branch>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:push — Gated Push to Fork

Read `../../rules/git-publish.md` first — remotes, pre-commit ≡ CI, and
PR-first landing are defined there. This skill only implements **branch
push to `origin`**.

- **`origin`** = personal fork — **only** allowed branch-push target.
- **`upstream`** = canonical MolCrafts repo — **never** push branches here
  (use `/mol:pr` after this skill).

## Iron law — pre-commit ≡ CI

No push until local hooks that mirror remote CI are green (full detail
in `git-publish.md`).

1. **Config** — `.pre-commit-config.yaml` present; else `/mol:ci-sync`. Still missing → BLOCK.
2. **Install** — `pre-commit --version` + `pre-commit install` (best-effort if `core.hooksPath` set). Missing binary → install via pipx/venv.
3. **Parity** — CI checks missing from pre-commit → `/mol:ci-sync`, re-run.
4. **Gate** — `pre-commit run --all-files` (full, not staged-only).

### Fix loop (≤ 3 cycles)

Parse failures → fix mechanical issues (`/mol:fix` / simplify / format) → re-run. Still red:

```
BLOCK PUSH — pre-commit still failing.

Options (user chooses):
  1. Keep fixing
  2. Push with --no-verify  (only if user says yes --no-verify / 用 --no-verify;
     refuse on default/release branch)
  3. Abort
```

Also run **`/mol:ship push`** (full suite / extras). Same 3-cycle budget if BLOCK.

## Procedure

1. **Branch** — `$ARGUMENTS` or current. Target remote = **`origin` only** (required).
2. **Remote guards**
   - No `origin` → stop hard.
   - Any attempt to push branches to `upstream` → stop hard; route `/mol:pr`.
   - If `upstream` exists and branch == upstream default → stop (never push the
     org default from a fork; feature/release branch only).
3. **Dirty tree** → `/mol:commit` first; BLOCK → stop.
4. **Iron law + ship** — green or user-approved `--no-verify`.
5. **Push** — `git push -u origin <branch>` (add `--no-verify` only if step 4 allowed).
   Never `--force` / `--force-with-lease`. Never tags (`/mol:tag`).
   Never `git push upstream …` for branches.
6. **Report** — branch, sha range, pre-commit green | BYPASSED; remind that
   landing on the org repo still requires `/mol:pr` (not a direct upstream push).

## Guardrails

- No green pre-commit (or explicit `--no-verify`) → no push.
- Never invent `--no-verify`; never force-push; **never push branches to `upstream`**.
- Prefer fix over bypass. Up-to-date + green → no-op success.
- This skill does **not** open a PR and does **not** update the org default branch.

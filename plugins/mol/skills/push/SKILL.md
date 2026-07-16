---
name: push
description: Push the current branch to origin after /mol:ship push. Auto-runs /mol:commit if dirty. No confirmation prompts. Never force-pushes; never pushes tags (use /mol:tag). Auto-invoked by /mol:pr and /mol-plugin:release.
argument-hint: "[<branch>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:push — Gated Push to Fork

Writes to a remote: `git push origin`. Standard GitHub fork-and-PR layout:

- **`origin`** = contributor's personal fork. Feature / release branches push here.
- **`upstream`** (when present) = canonical org-owned repo. Branches **never** push here from this skill — reach upstream only via `/mol:pr` (+ merge).

**Fully agent-driven** — no confirmation prompts.

## Procedure

### 1. Resolve branch and remote

- Branch: `$ARGUMENTS` if provided, else current (`git rev-parse --abbrev-ref HEAD`).
- Push target = `origin`. Missing → stop hard.

Single-remote (no `upstream`) → push to `origin` without asking.

### 2. Default-branch guard (forks only)

`upstream` exists and current branch == upstream default → **stop hard** (do not push default from a fork). Create/switch to a feature or release branch instead — no user prompt, report the stop.

No `upstream` → skip.

### 3. Commit pending work first

`git status --porcelain` non-empty → invoke `/mol:commit` (no prompt). BLOCK → stop.

Clean tree → skip.

### 4. Run the push gate

Invoke `/mol:ship push`.

**BLOCK** → stop with blocker (attempt `/mol:fix` once if clearly mechanical; else stop).
**PROCEED** → continue.

### 5. Push

```
git push -u origin <branch>
```

Never `--force` / `--force-with-lease`.

### 6. Report

```
/mol:push: pushed <branch> → origin/<branch>
  <short-sha-range>
```

## Guardrails

- **Never** push to `upstream`.
- **Never** force-push.
- **Never** push the default branch from a fork.
- **Never** skip `/mol:ship push`.
- **Never** push tags — `/mol:tag` only.
- **Never** wait for confirmation.

## Idempotency

Up-to-date branch → no-op success.

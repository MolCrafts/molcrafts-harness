---
name: commit
description: Stage safe changes and commit after the /mol:ship commit gate. Auto-stages non-secret paths, auto-generates the message when none is supplied, never waits for approval. Never pushes; commits are local-only. Auto-invoked by /mol:push, /mol:impl, /mol:close, /mol:release, /mol-plugin:release.
argument-hint: "[<message>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:commit — Gated Local Commit

Write skill: stages files + creates a commit. Pushing is `/mol:push`.

Contract: no commit without a passing pre-commit gate. Gate lives in `/mol:ship commit`. **Fully agent-driven** — never waits for the user.

## Procedure

### 1. Sanity check

`git status --porcelain` empty → stop, report nothing to commit.

### 2. Stage automatically

- Already staged → keep; also stage any remaining unstaged **safe** paths needed for a coherent commit of the current work.
- Nothing staged + changes exist → stage every changed/untracked path **except** secret/binary refuse list:

  Refuse (never stage; strip if already staged and abort that path):
  `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa*`, `*.p12`, credentials files, obvious secret names.

Stage by explicit paths from `git status` (never blind `git add -A` on unknown trees when secret-looking paths exist; when the refuse list is empty, `git add -A` is allowed).

Do **not** ask the user which files to include.

### 3. Run the pre-commit gate (CI parity)

1. Ensure `.pre-commit-config.yaml` exists and hooks are installed
   (`pre-commit install` if `.git/hooks/pre-commit` missing). Missing config →
   invoke `/mol:ci-sync` first. Still missing → **BLOCK**, do not commit.
2. Run staged hooks the way git will: either rely on the upcoming
   `git commit` hook run, or proactively:

   ```
   pre-commit run
   ```

   On failure → fix and re-stage, up to 3 cycles. Still red → **BLOCK**
   (do not offer `--no-verify` here; that escape hatch lives only on
   `/mol:push` after the user explicitly accepts).
3. Invoke `/mol:ship commit` for any extra commit-tier checks not in hooks.

- **BLOCK** → fix when mechanical; re-run. Still BLOCK → stop. Do not commit.
- **PROCEED** → continue.

### 4. Resolve the commit message

`$ARGUMENTS` non-empty → use as commit subject (no approval).

Else generate conventional-commit message from staged diff and **use it immediately** (no approval wait):

- Type: `feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `perf` / `ci`.
- Subject: ≤ 72 chars, imperative, no trailing period.
- Body optional when non-obvious.

### 5. Commit

```
git commit -m "<subject>" [-m "<body>"]
```

Never `--no-verify` / `--no-gpg-sign` / `--amend` from this skill (close may amend its own close commit only). **`--no-verify` is forbidden in commit** — fix the hooks or stop; push-time bypass is a separate, user-gated decision on `/mol:push`. Pre-commit hook fails despite PROCEED → fix, re-stage, re-run `/mol:commit`.

### 6. Report

```
/mol:commit: committed <short-sha> on <branch>
  <subject>
```

No "please push" prompt — callers chain `/mol:push` when needed.

## Guardrails

- **Do not** `git push` (use `/mol:push`).
- **Do not** skip hooks (`--no-verify` is never used by this skill).
- **Do not** wait for message or path approval.
- **Do** keep pre-commit hooks CI-parity (same commands as the remote workflow).
- **Do not** commit secret paths (refuse list above).
- **Do not** amend — always new commit (except callers that own an atomic amend protocol, e.g. `/mol:close`).

## Idempotency

Clean tree → no-op ("nothing to commit").

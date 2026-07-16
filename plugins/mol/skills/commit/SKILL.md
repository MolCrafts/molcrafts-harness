---
name: commit
description: Stage and commit changes after running the /mol:ship commit gate (format + lint + pre-commit hooks). Refuses to commit when the gate reports BLOCK. Generates a conventional-commit message from the staged diff if the user does not supply one. Never pushes; commits are local-only.
argument-hint: "[<message>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:commit — Gated Local Commit

Write skill: stages files + creates a commit. Pushing is `/mol:push`.

Contract: no commit without a passing pre-commit gate. Gate lives in `/mol:ship commit`.

## Procedure

### 1. Sanity check

`git status --porcelain` empty → stop, report nothing to commit.

### 2. Decide what to stage

- Already staged → treat as commit contents; do not auto-add unstaged.
- Nothing staged + unstaged changes exist → list them, ask user to `git add` all or pick subset. Never `git add -A` / `git add .` silently (risks `.env`, credentials, large binaries).

Stage by exact paths only. Never `-A` / `.` / globs.

### 3. Run the pre-commit gate

Invoke `/mol:ship commit`.

- **BLOCK** → stop, relay top blocker + recommended `/mol:fix` (or `/mol:impl` / `/mol:refactor`) action. Do not commit.
- **PROCEED** → continue.

### 4. Resolve the commit message

`$ARGUMENTS` non-empty → use as commit subject.

Else generate conventional-commit message from staged diff:

- Type (inferred from paths): `feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `perf` / `ci`.
- Subject: ≤ 72 chars, imperative, no trailing period.
- Body (optional): wrap at 72 cols, explain *why* not *what* when non-obvious.

Show proposed message; wait for approval (user may edit inline).

### 5. Commit

```
git commit -m "<subject>" [-m "<body>"]
```

Never `--no-verify` / `--no-gpg-sign` / `--amend`. Pre-commit hook fails despite PROCEED → real signal: surface output, fix, re-stage, re-run `/mol:commit`. Do **not** amend (failed commit means no commit, so amend mutates *previous* commit).

### 6. Report

Emit the one-line F2 summary plus a next-step pointer:

```
/mol:commit: committed <short-sha> on <branch>
  <subject>

next: /mol:push   (push to origin = your fork)
```

## Guardrails

- **Do not** `git push` (use `/mol:push`).
- **Do not** stage with `-A` / `.` / globs.
- **Do not** skip hooks (`--no-verify`).
- **Do not** amend — always new commit.
- **Do not** commit `.env`, credentials, `*.key` / `*.pem` / `id_rsa*` even if staged — warn and require explicit confirmation.

## Idempotency

Clean tree → no-op ("nothing to commit"). Two runs commit twice only if new staged changes between; otherwise second run is no-op.

---
name: pr
description: Open a pull request from origin (fork) to upstream (canonical). Calls /mol:push first. Never land on org default without a PR. Auto-drafts title/body and creates the PR with no approval wait. Auto-invoked by /mol:release and /mol-plugin:release.
argument-hint: "[<title>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:pr — Pull Request from Fork to Upstream

Read `../../rules/git-publish.md` first — PR-first landing is the only
legal path onto the canonical default branch.

Creates a GitHub PR. Base = `upstream` / `<default_branch>`; head =
`origin` (fork). **Fully agent-driven** — no title/body approval wait.

## Procedure

### 1. Resolve config

- **Origin** must exist. Else stop hard.
- **Upstream**: absent + origin is a fork → `git remote add upstream <parent-url>`
  automatically. Absent + origin not a fork → stop hard (no PR target;
  single-remote repos land by push only after ship gates — do not invent
  an upstream).
- **Branch**: current branch. Default branch as head → stop hard (switch
  to feature/release branch first).

Resolve upstream default branch via `upstream/HEAD` or `main`/`master`.

### 2. Verify gh

`gh auth status`. Unauthenticated → stop hard with `gh auth login`
instruction (cannot auto-login interactively).

### 3. Push first (fork only)

Invoke `/mol:push`. Blocker → stop. That step already enforces
pre-commit ≡ CI and **origin-only** branch push.

### 4. Draft title and body (no approval)

Compare `upstream/<default_branch>..HEAD`.

`$ARGUMENTS` non-empty → PR title. Else derive from commits. Body:

```
## Summary
- <bullets why>

## Test plan
- [x] local pre-commit ≡ CI + /mol:ship push
- [ ] CI on the PR (must be green before merge)
```

**Do not wait** for user edit. Create immediately.

### 5. Existing PR

Open PR for this branch → report URL, no-op (idempotent).

### 6. Create

```
gh pr create \
  --base "<default_branch>" \
  --repo "<upstream-owner>/<upstream-repo>" \
  --title "<title>" \
  --body "<body>"
```

Head is the current branch on `origin` (fork). Never create a PR that
would push or update `upstream` branches outside GitHub's PR flow.

### 7. Report

```
/mol:pr: opened PR <number> against upstream/<default_branch>
  <url>
  next: wait for green checks, then merge (release chain does this)
```

## Guardrails

- **Never** create PR with default branch as head.
- **Never** skip `/mol:push`.
- **Never** wait for title/body approval.
- **Never** force-assign reviewers.
- **Never** `git push upstream` as a substitute for opening a PR.
- Landing on the org default without a PR is forbidden (`git-publish.md`).

## Idempotency

Open PR already exists → report URL, success no-op.

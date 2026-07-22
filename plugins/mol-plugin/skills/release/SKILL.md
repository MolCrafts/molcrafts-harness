---
name: release
description: Unified marketplace release — bump all plugin manifests, commit, push origin (fork) after pre-commit≡CI, PR to upstream, wait green checks, merge, tag. Never direct-push branches to upstream. User-only. Not for product libraries (/mol:release).
disable-model-invocation: true
argument-hint: "<patch | minor | major>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol-plugin:release — Marketplace Release

Unified cut of **all** plugins under `plugins/` (mol, molexp, mol-plugin, …).
Product libraries use `/mol:release`.

**Same publish invariants as ecosystem release** — read
`plugins/mol/rules/git-publish.md` before running:

| Law | Rule |
|---|---|
| Remotes | `origin` = fork (branch push only); `upstream` = canonical (PR + merge only) |
| pre-commit ≡ CI | Full local hooks + `/mol:ship push` before any network push |
| PR-first | Never `git push upstream <branch>`; never land on org default without a PR |
| Green merge | Wait for PR checks; never merge red CI (avoids Actions email storms) |

Write surface: every `plugins/*/.{claude,codex}-plugin/plugin.json`,
`.claude-plugin/marketplace.json` versions, commit + local tag, then the
publish chain. No CHANGELOG. `.agents/plugins/marketplace.json` has no
version field — leave it.

## Procedure

### 1. Args

`<bump>` ∈ `patch|minor|major`.

### 2. Tree

Dirty → `/mol:commit` auto. BLOCK → stop.

### 3. Validate

`/mol-plugin:check`. 🚨/🔴 → stop. 🟡/AMBIGUITY → proceed and list.

### 4. Version

All plugin + marketplace versions must agree; bump together. Local tag
`v<new>` must not exist on the release remote.

### 5. Branch + commit + local tag

`git switch -c release/v<new>` (or switch if exists). Write all
plugin.json + marketplace versions →
`/mol:commit "release: v<new>"` →
`git tag -a v<new> -m "release: v<new>"`.

### 6. Publish chain (no direct upstream branch push)

1. **`/mol:push`** → **origin only** (enforces pre-commit ≡ CI + `/mol:ship push`)
2. **`/mol:pr`** title `release: v<new>` (base = `upstream/<default>`)
3. **Wait for green PR checks** — `gh pr checks <n> --watch` (or poll).
   Red or timeout → **BLOCK**; do not merge; report failures.
4. **`gh pr merge <n> --merge`** — prefer merge commit; **no `--admin`**
   unless checks are already green and the only blocker is admin-only
   protection. **Never** override red CI.
5. If tag not on `upstream/<default>` after squash: retag at that tip
6. **`/mol:tag v<new>`** (tag ref only → upstream)
7. Switch default, pull upstream, delete merged `release/v<new>` locally
   and on origin

### 7. Report

```
/mol-plugin:release: v<old> → v<new>
  plugins: N / PR: <url> / checks: green / tag: <remote>
```

## Guardrails

- Never force-overwrite remote tags; never CHANGELOG; never wait for approval.
- Never advance a subset of plugins. Merge-commit preferred for tag SHA.
- **Never** push the release branch (or any branch) to `upstream` —
  always fork → PR → green checks → merge.
- **Never** merge while PR checks are red or pending.
- Never use for product-library versions (`/mol:release`).
- Idempotent if version + tag already on upstream.

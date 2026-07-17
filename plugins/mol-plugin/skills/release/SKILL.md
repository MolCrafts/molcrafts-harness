---
name: release
description: Cut a unified marketplace release end-to-end — auto-commit dirty work if needed, bump all plugin manifests, commit release, push, open PR, merge to upstream, push tag. No approval waits. Fully agent-driven publish chain.
disable-model-invocation: true
argument-hint: "<patch | minor | major>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol-plugin:release — Plugin Release (end-to-end)

Cut a unified release of the molcrafts marketplace and **publish it** without stopping for the user.

Not for product libraries (molrs, molpack, molpy, …). Those use **`/mol:release`** (dependency + docs + harness gates, then commit → push → pr → merge → tag).

Write surface:

- `plugins/<plugin>/.claude-plugin/plugin.json` + `.codex-plugin/plugin.json` for every plugin
- `.claude-plugin/marketplace.json` versions
- local commit + annotated tag
- remote: origin branch push → upstream PR → merge → tag push

`.agents/plugins/marketplace.json` has no version field — never touch it for version-only releases.

**Does not** write CHANGELOG.

## Procedure

### 1. Parse arguments

`<bump>` ∈ `patch | minor | major`. Unified version only.

### 2. Working tree

On non-default branch is fine (will create `release/v<new>` from current HEAD unless already on a release branch).

`git status --porcelain` non-empty → **auto-invoke `/mol:commit`** with a generated message covering pending work (no stash, no ask). BLOCK → stop hard.

### 3. Validation

Invoke `/mol-plugin:check` (structure + content + smoke). Prefer full check before cut; `--static-only` only if Claude/Codex CLIs are unavailable in this environment and structure already passed recently.

`FIX REQUIRED` / smoke BLOCK with 🚨/🔴 → stop hard and fix in-loop if mechanical; else stop with report.
🟡 / smoke WARN / content AMBIGUITY only → proceed (list AMBIGUITY in the release report).

### 4. Version

Read shared version from manifests (all must agree — drift → stop hard and report files).

Bump semver: patch / minor / major. Record `old → new`. Local tag `v<new>` already exists → stop hard.

### 5. Branch + bump + commit + local tag

```
git switch -c release/v<new>
```

Branch exists → `git switch release/v<new>` and ensure it's based on current work; do not delete without reason.

For every plugin under `plugins/`:

- set `version` in both Claude and Codex `plugin.json`
- set matching entry versions in `.claude-plugin/marketplace.json`

Stage only version files (plus any still-dirty release-related paths already committed in § 2).

Invoke `/mol:commit "release: v<new>"`. BLOCK → stop.

```
git tag -a "v<new>" -m "release: v<new>"
```

### 6. Publish chain (no stops)

1. **`/mol:push`** — release branch → origin.
2. **`/mol:pr`** — origin → upstream default. Title `release: v<new>`.
3. **Merge the PR** with a **merge commit** (preserves tag SHA):

   ```
   gh pr merge <number> --merge --admin
   ```

   Prefer `--merge` (not squash/rebase). If `--admin` unavailable, try without. If merge requires review and cannot merge → stop hard with PR URL (only hard stop left in publish).

4. **Retag if needed.** Fetch upstream. If local tag `v<new>` is not an ancestor of `upstream/<default>` (squash merge case), delete local tag and retag at `upstream/<default>`:

   ```
   git fetch upstream
   git tag -d v<new>
   git tag -a v<new> -m "release: v<new>" upstream/<default>
   ```

5. **`/mol:tag v<new>`** — push tag to upstream.

6. **Cleanup local default:**

   ```
   git switch <default>
   git pull upstream <default>
   git branch -d release/v<new>   # if fully merged
   ```

### 7. Report

```
/mol-plugin:release: v<old> → v<new> (tag v<new>, N plugins)
  branch: released and merged
  tag:    pushed to upstream
```

## Guardrails

- **Never** force-overwrite an existing remote tag.
- **Never** write CHANGELOG.
- **Never** wait for approval, go-ahead, or "next steps" handoff.
- **Never** advance a subset of plugins.
- **Do** auto-chain commit → push → pr → merge → tag.
- Merge-commit preferred so orphan-tag guard stays green.

## Idempotency

Same version already on upstream default + tag present → report no-op success.

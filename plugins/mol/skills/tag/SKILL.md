---
name: tag
description: Push an existing local release tag to upstream so the release workflow fires. Auto after /mol:release or /mol-plugin:release has merged the version-bump commit. No approval wait when safety checks pass. Refuses orphan tags and force overwrites.
argument-hint: "[<tag>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:tag — Push Release Tag to Upstream

Push the release tag (only the tag) to `upstream` (or `origin` when single-remote). **Fully agent-driven** when safety checks pass.

## Procedure

### 1. Resolve config

- `upstream` exists → push target = `upstream`.
- Only `origin` → push target = `origin` (no prompt).

### 2. Pick the tag

`$ARGUMENTS` if set; else most recent local tag not on the release remote matching `v*`.

### 3. Verify the tag (hard gates — no prompt override)

- Tag exists locally.
- Subject of tagged commit matches `^release: v` (else stop hard with reason).
- Tag not already on release remote (else no-op success if same SHA; stop if different).
- **Orphan-tag guard:** tagged commit reachable from release-remote default branch. Fail → stop hard with recovery steps (do **not** wait for user choice; report what failed). Release must merge first.

### 4. Push the tag

```
git push <release-remote> <tag>
```

Never `--force`. Never `git push --tags`.

### 5. Report

```
/mol:tag: pushed <tag> → <release-remote>
  commit: <short-sha> <subject>
```

## Guardrails

- **Never** force-push a tag.
- **Never** create tags here (creation is `/mol:release` or `/mol-plugin:release`).
- **Never** push orphan tags.
- **Never** wait for approval when checks pass.

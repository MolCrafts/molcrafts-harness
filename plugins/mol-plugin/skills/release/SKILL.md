---
name: release
description: Unified marketplace release — bump all plugin manifests, commit, push, PR, merge, tag. User-only. Not for product libraries (/mol:release).
disable-model-invocation: true
argument-hint: "<patch | minor | major>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol-plugin:release — Marketplace Release

Unified cut of **all** plugins under `plugins/` (mol, molexp, mol-plugin, …). Product libraries use `/mol:release`.

Write surface: every `plugins/*/.{claude,codex}-plugin/plugin.json`, `.claude-plugin/marketplace.json` versions, commit + tag, origin push → upstream PR → merge → tag push. No CHANGELOG. `.agents/plugins/marketplace.json` has no version field — leave it.

## Procedure

1. **Args** — `<bump>` ∈ `patch|minor|major`.
2. **Tree** — dirty → `/mol:commit` auto; BLOCK → stop.
3. **Validate** — `/mol-plugin:check`. 🚨/🔴 → stop. 🟡/AMBIGUITY → proceed and list.
4. **Version** — all plugin + marketplace versions must agree; bump together. Local tag `v<new>` must not exist.
5. **Branch** — `release/v<new>`; write all plugin.json + marketplace versions; `/mol:commit "release: v<new>"`; `git tag -a v<new> -m "release: v<new>"`.
6. **Publish** — `/mol:push` → `/mol:pr` → `gh pr merge --merge --admin` → retag if squash → `/mol:tag v<new>` → pull default, delete release branch.
7. **Report** — `v<old> → v<new>`, plugin count, tag remote.

## Guardrails

- Never force-overwrite remote tags; never CHANGELOG; never wait for approval.
- Never advance a subset of plugins. Merge-commit preferred for tag SHA.
- Idempotent if already released on upstream.

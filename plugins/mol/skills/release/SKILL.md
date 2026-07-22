---
name: release
description: Ecosystem library release end-to-end — first-party dep/registry gates, docs + harness currency, version bump, then /mol:commit → push → pr → merge → /mol:tag. User-only. Distinct from /mol-plugin:release (marketplace).
disable-model-invocation: true
argument-hint: "<patch | minor | major> [<package-or-manifest path>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:release — Ecosystem Package Release

Product libraries (molrs, molpack, molpy, molvis, molexp, …): version bump → commit → push → PR → merge → tag. Prefer tag-triggered CI for crates.io / PyPI / npm — do not publish inline unless the project has no tag workflow.

| Skill | Releases |
|---|---|
| **`/mol:release`** | Ecosystem packages |
| **`/mol-plugin:release`** | This marketplace only |

**Never write CHANGELOG** — history is `git log`; GitHub Release auto-notes.

## Procedure

### 1. Args

`<bump>` ∈ `patch|minor|major`. Optional path to package/manifest; empty → root/workspace published product.

### 2. Tree

Dirty → `/mol:commit` auto. BLOCK → stop. Non-default branch OK.

### 3. Hard gates (any 🚨 → stop)

**3a. First-party deps** — inventory sibling MolCrafts deps (ignore pure third-party / unpublished workspace members).

| Ecosystem | BLOCK if |
|---|---|
| Cargo | path-only (no `version`) |
| Python/npm runtime | still `file:` / `link:` / path editable on published surface |
| Pin vs local sibling | local version doesn't satisfy pin |
| Registry | pin version missing on crates.io/PyPI/npm (network fail = BLOCK) |

Emit publish order (deps → this). Cycle among separately published packages → BLOCK. Cargo path+version dual-pin OK.

**3b. Docs** — since last tag: public API/CLI/install commits must have matching `docs/` or README (no "TODO document"). Version badges/snippets updated with the bump in § 5. No CHANGELOG required.

**3c. Harness** — if sibling `molcrafts-harness` exists: dirty or untagged commits that this package's harness relies on → BLOCK until `/mol-plugin:release`. Missing checkout → 🟡 skip.

**3d. CI** — `/mol:ship push`. BLOCK → ≤3 fix cycles or stop.

### 4–5. Version + branch + commit + local tag

Read versions; bump semver; local tag `v<new>` must not exist. `git switch -c release/v<new>` (or switch if exists).

Update only publish surface: crate/py/npm version fields; README badges that hardcode version. **Never** CHANGELOG. Stage release paths → `/mol:commit "release: v<new>"` → `git tag -a v<new> -m "release: v<new>"`.

### 6. Publish chain (no stops)

1. `/mol:push` → origin  
2. `/mol:pr` title `release: v<new>`  
3. `gh pr merge <n> --merge --admin` (prefer merge commit; try without `--admin` if needed)  
4. If tag not on `upstream/<default>` after squash: retag at that tip  
5. `/mol:tag v<new>`  
6. Switch default, pull upstream, delete merged `release/v<new>`  

### 7. Report

```
/mol:release: v<old> → v<new>
  package / deps / docs / harness / tag / publish path
```

## Guardrails

- Never force-overwrite remote tags; never skip gates; never wait for approval.
- Never use inside `molcrafts-harness` for marketplace versions (`/mol-plugin:release`).
- Dependent after dependency on registry. Idempotent if version+tag already on upstream.

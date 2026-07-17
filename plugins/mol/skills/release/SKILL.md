---
name: release
description: Cut an ecosystem library release end-to-end — hard-gate first-party path/editable deps and registry versions, check docs + harness currency, bump package version, then chain /mol:commit → push → pr → merge → /mol:tag. Fully agent-driven. Distinct from /mol-plugin:release (harness marketplace only).
disable-model-invocation: true
argument-hint: "<patch | minor | major> [<package-or-manifest path>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:release — Ecosystem Package Release (end-to-end)

Cut a **product library** release (molrs, molpack, molpy, molvis, molexp, …) and **publish the git side** without stopping for the user: version bump → commit → push → PR → merge → tag.

| Skill | Releases |
|-------|----------|
| **`/mol:release`** | Ecosystem packages → crates.io / PyPI / npm (via tag-triggered CI or post-tag publish) |
| **`/mol-plugin:release`** | This harness marketplace only (`molcrafts-harness` plugins) |

**Does not** run `cargo publish` / `twine` / `npm publish` inline unless the project's documented release path is local-only and has no tag workflow — prefer tag → CI.

**Never write a CHANGELOG.** Change history is `git log` between tags; the GitHub Release page auto-generates notes from that. Do not create, fill, or rename `CHANGELOG*` / `CHANGES*` / keep-a-changelog sections as part of this skill.

## Procedure

### 1. Parse arguments

```
<bump> [path]
```

- `<bump>` ∈ `patch | minor | major` — required.
- `[path]` optional package dir or manifest (e.g. `python/`, `molrs/Cargo.toml`). Empty → workspace / root package(s) that constitute the published product.

### 2. Working tree

On non-default branch is fine (will create `release/v<new>` from current HEAD unless already on a release branch).

`git status --porcelain` non-empty → **auto-invoke `/mol:commit`** with a generated message covering pending work (no stash, no ask). BLOCK → stop hard.

### 3. Hard gates (all must pass — any 🚨 → stop)

Run in order. Fix mechanical issues in-loop when safe; otherwise stop with the gate report.

#### 3a. First-party dependency sources + versions

Cross-repo MolCrafts packages often develop against siblings via local sources. Releasing while a dep is still path-only, or while the pin names a version not on the registry (or disagrees with the sibling you built against), ships a package nobody can install. **Dependencies first; then dependents.**

| Ecosystem | Local-dev form | Publish-ready form |
|-----------|----------------|--------------------|
| Cargo | `path = "../molrs/molrs"` | also has `version = "…"` (path may stay for local builds) |
| Python | `pip install -e ../x`, `file://`, path tables | registry pin e.g. `molrs>=0.8.0` on the **published** requires |
| npm | `file:`, `link:`, residual `npm link` | semver on registry; no `file:`/`link:` on runtime deps |

**Inventory** first-party / sibling deps from manifests (Cargo.toml, pyproject, package.json, …). Ignore pure third-party (`serde`, `numpy`, …). Intra-workspace members that are **not** separately published → ignore.

**Gate A — source shape**

- Cargo **path-only** (no `version`) → 🚨 BLOCK.
- Cargo **path + version** → OK for dual-pin practice; continue.
- Python/npm **runtime** surface still local (`file:`, `link:`, path/editable in published metadata) → 🚨 BLOCK. Dev-only editables → 🟡 only.

**Gate B — pin ↔ local sibling**

When a sibling checkout is resolvable (path field or obvious adjacent repo): local package version `L` must match exact pin `V`, or satisfy a range pin. Mismatch → 🚨 BLOCK.

**Gate C — pin on official registry**

Query crates.io / PyPI / npm for each first-party `(name, version)` (ranges → check the minimum). Missing → 🚨 BLOCK: publish that dependency first, re-run `/mol:release`. Network failure → 🚨 BLOCK (unknown registry state is not OK).

Emit a short **publish order** (deps → this package). Cycle among separately published packages → 🚨 BLOCK.

#### 3b. Docs currency

Release notes are **not** hand-written: use `git log <prev-tag>..HEAD` as the change record; GitHub Release auto-generates the changelog. **Do not** require or edit a `CHANGELOG` file. If a stale `CHANGELOG*` exists in the tree, ignore it for this gate (do not update it; do not BLOCK for missing entries).

Since the previous release tag (or repo root if none):

1. **Public docs** (`docs/`, README install/API sections): if commits touch public API / CLI / install surface, corresponding docs or README must already reflect the change (no “TODO document before release”). Drift → 🚨 BLOCK with paths.
2. **Version badges / install snippets** in README that hardcode a version must match `v<new>` after the bump (update in § 5 with the version files).

No public-doc surface and only internal commits → pass with 🟡 note.

#### 3c. Harness currency (`molcrafts-harness`)

Product releases must not depend on **unreleased** harness work.

1. Locate harness checkout: sibling directory `molcrafts-harness` (or `../molcrafts-harness`), or an explicit path from project notes / env. Missing → 🟡 skip with “confirm harness already released”; do not invent a path.
2. When found:
   - Read harness latest release tag / marketplace shared version.
   - If harness working tree is dirty **or** has commits on its default branch not in the latest `v*` tag that touch `plugins/mol/` (skills, agents, rules) or marketplace manifests **and** this package’s `.claude/` / `CLAUDE.md` / notes clearly rely on those unreleased surfaces → 🚨 BLOCK: run `/mol-plugin:release` on the harness first, then re-run `/mol:release`.
   - If harness is clean at a published tag and this package does not require unreleased skills → pass.
3. Project harness health: `CLAUDE.md` has `mol_project:` when the project uses mol; missing with an existing `.claude/` tree → 🟡 suggest `/mol:bootstrap` (do not block a pure library tag unless release notes claim new skill support).

#### 3d. CI parity

Invoke `/mol:ship push` (or project-equivalent full local gate). BLOCK → fix loop (≤ 3 cycles) or stop hard.

### 4. Version

Read current package version(s) from the scoped manifest(s). Multi-crate / dual Rust+Python products: all **published** artifacts that share a product line must agree or have a documented mapping in CLAUDE.md; unexplained drift → stop hard.

Bump semver: patch / minor / major. Record `old → new`. Local tag `v<new>` already exists → stop hard.

### 5. Branch + bump + commit + local tag

```
git switch -c release/v<new>
```

Branch exists → `git switch release/v<new>` and ensure it carries current work; do not delete without reason.

Update version fields only where this product publishes:

- Rust: `[package].version` in the releasing crate(s); path-dep `version =` pins **on dependents are not auto-edited** (other repos run their own `/mol:release`).
- Python: `project.version` / hatch / setuptools equivalent.
- npm: `package.json` `"version"` (and workspace package being released).
- README badges / install pins that hardcode the old version → update to `new` when present.
- **Never** create or edit `CHANGELOG*` / keep-a-changelog files.

Stage release-related paths only (plus any still-dirty paths already meant for this cut from § 2).

Invoke **`/mol:commit "release: v<new>"`**. BLOCK → stop.

```
git tag -a "v<new>" -m "release: v<new>"
```

### 6. Publish chain (no stops)

Same shape as `/mol-plugin:release`:

1. **`/mol:push`** — release branch → origin.
2. **`/mol:pr`** — origin → upstream default. Title `release: v<new>`.
3. **Merge the PR** with a **merge commit** (preserves tag SHA):

   ```
   gh pr merge <number> --merge --admin
   ```

   Prefer `--merge` (not squash/rebase). If `--admin` unavailable, try without. Merge requires review and cannot merge → stop hard with PR URL.

4. **Retag if needed.** Fetch upstream. If local tag `v<new>` is not on `upstream/<default>` (squash case), delete local tag and retag at `upstream/<default>`:

   ```
   git fetch upstream
   git tag -d v<new>
   git tag -a v<new> -m "release: v<new>" upstream/<default>
   ```

5. **`/mol:tag v<new>`** — push tag to upstream (fires `on: push: tags` publish workflows when configured).

6. **Cleanup local default:**

   ```
   git switch <default>
   git pull upstream <default>
   git branch -d release/v<new>   # if fully merged
   ```

### 7. Report

```
/mol:release: v<old> → v<new> (tag v<new>)
  package:  <name> (<manifest>)
  deps:     all first-party pins on registry (or N/A)
  docs:     ok
  harness:  ok | skipped (no checkout) | blocked reason
  branch:   released and merged
  tag:      pushed to upstream
  publish:  tag-triggered CI | note if operator must run registry publish manually
```

## Guardrails

- **Never** force-overwrite an existing remote tag.
- **Never** write, update, or require a hand-maintained CHANGELOG — history is git log; GitHub Release auto-notes own the user-facing changelog.
- **Never** wait for approval, go-ahead, or “next steps” handoff.
- **Never** skip gates 3a–3d to “just tag”.
- **Never** use this skill inside `molcrafts-harness` for plugin marketplace versions — that is `/mol-plugin:release`.
- **Never** publish a dependent before its first-party dependency exists on the registry.
- **Do** auto-chain commit → push → pr → merge → tag.
- **Do** keep Cargo dual-pin (`path` + `version`) when that is the project convention; only path-only is forbidden.
- Merge-commit preferred so `/mol:tag` orphan-tag guard stays green.

## Idempotency

Same version already on upstream default + tag present on release remote → report no-op success.

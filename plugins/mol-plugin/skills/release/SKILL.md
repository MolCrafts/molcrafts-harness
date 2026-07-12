---
description: Cut a unified release of the molcrafts marketplace — bumps every plugin's `plugin.json` + matching `marketplace.json` entries (all plugins share one version), runs `/mol-plugin:check`, and prepares one local commit + tag `v<X.Y.Z>`. Does not push; pair with `/mol:push` + `/mol:pr` + `/mol:tag` to publish.
argument-hint: "<patch | minor | major>"
---

# /mol-plugin:release — Plugin Release

Cut a unified release of the molcrafts marketplace. All plugins share one version; one bump advances them all + produces one tag.

Write surface:

- `plugins/<plugin>/.claude-plugin/plugin.json` (`version` field) for every plugin
- `.claude-plugin/marketplace.json` (matching `version` for every plugin entry)
- one git commit + one git tag (when user opts in)

**Does not** write CHANGELOG. Release notes live on the GitHub release + `git log`.

## Procedure

### 1. Parse arguments

Form: `<bump>` ∈ `patch | minor | major`. No plugin selection — releases are unified. Wanting to ship one plugin → unified-version policy is wrong; raise as design change, don't simulate.

### 2. Confirm clean tree

`git status --porcelain` empty; else stop, ask user to commit/stash. Confirm on default branch (warn if not).

### 3. Run validation

Invoke `/mol-plugin:check`. Verdict `FIX REQUIRED` → stop (user can override with explicit confirmation).

### 4. Compute the new version

- Read shared version from any `plugin.json` (must agree; drift → § 5).
- Bump per level (semver: `0.1.3` + patch → `0.1.4`, + minor → `0.2.0`, + major → `1.0.0`).
- Record old → new.

### 5. Drift detection

Any plugin's `plugin.json` differs from others (or from its `marketplace.json` entry) → stop. Report which plugins are out of sync. User either:

- aligns by hand and re-runs, or
- asks for separate "drift fix" commit, then re-runs on aligned tree.

Never silently absorb drift.

### 6. Reach approval

Show:

- old → new shared version
- proposed commit message (`release: v<new>`)
- proposed tag (`v<new>`)
- list of plugins being advanced (visibility only)

Wait for go-ahead.

### 7. Apply

**Switch to a release branch first.** Release commit + tag live on `release/v<new>`, not `master`:

- `/mol:push` refuses to push the default branch from a fork.
- Master stays untouched until PR merges; botched release = deletable branch.

```
git switch -c release/v<new>
```

`release/v<new>` already exists locally → stop. User deletes (`git branch -D release/v<new>`) and re-runs.

For every plugin under `plugins/`:

- write `plugin.json` with new version
- update entry in `.claude-plugin/marketplace.json` with same new version

Stage:

```
git add plugins/*/.claude-plugin/plugin.json
git add .claude-plugin/marketplace.json
```

Invoke `/mol:commit "release: v<new>"` — it runs the `/mol:ship commit` gate itself (no separate `/mol:ship` call here; that would double-run the gate). **BLOCK** → stop and surface blocker. Approval was already collected in § 6, so confirm the shown message unchanged. After the commit lands:

```
git tag v<new>
```

Tag creation stays here — `/mol:commit` never tags. One commit, one tag, on `release/v<new>`. Master untouched. **Do not push** — publish phase is § 8.

### 8. Report

One-line summary: `released v0.1.1 → v0.1.2 (tag v0.1.2, N plugins advanced)`

Print **publish sequence** (order is load-bearing):

```
Next steps to publish v<new>:

  (you are on release/v<new>; master is untouched)

  1. /mol:push                 # push release/v<new> to origin (fork)
  2. /mol:pr                   # open PR origin → upstream/master
  3. (wait for PR to merge into upstream/master)
  4. /mol:tag                  # push the tag — refuses if step 3
                               # hasn't happened (orphan-tag guard)
  5. cleanup:
       git switch master
       git pull upstream master
       git branch -d release/v<new>

Step 4's orphan-tag guard, the merge-style caveat (prefer a
merge-commit merge; squash/rebase orphans the local tag), and the
recovery paths are owned by /mol:tag Step 3 — see
plugins/mol/skills/tag/SKILL.md. Short version: the version bump
lives in the release *commit* (must merge first); the *tag* push
triggers the release workflow.
```

Single-remote layouts (no `upstream`) collapse 1–3 to one `git push` to the canonical default branch (still from `release/v<new>`, then fast-forward master locally); two phases (branch then tag) still apply.

## Guardrails

- **Do not** push to a remote.
- **Do not** force-overwrite an existing tag. `v<new>` already exists → stop.
- **Do not** create or modify any CHANGELOG file.
- **Do not** release if `/mol-plugin:check` reports `FIX REQUIRED` without explicit user override.
- **Do not** advance a subset of plugins.

## Idempotency

Same version twice = error (tag collision stops run). Redo a botched release → user deletes the tag manually (locally + remotely) and re-runs; this skill does not delete tags.

Run reaching approval gate + rejected → tree exactly as found. No file writes before approval.

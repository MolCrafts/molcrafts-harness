---
description: Cut a unified release of the molcrafts marketplace. All plugins share one version. Bumps every plugin's plugin.json + the matching marketplace.json entries together, runs /mol-plugin:check, gates the commit through /mol:ship commit, and prepares one local commit + one local tag named v<X.Y.Z>. Does not push — pair with /mol:push + /mol:pr to publish the marketplace.json bump through upstream's default branch, then /mol:tag to push the tag and trigger the GitHub Actions release workflow. Writes plugin.json files and marketplace.json only — never a CHANGELOG.
argument-hint: "<patch | minor | major>"
---

# /mol-plugin:release — Plugin Release

Cut a unified release of the molcrafts marketplace. Every plugin
shares the same version; one bump advances them all and produces
a single tag.

This skill writes only:

- `plugins/<plugin>/.claude-plugin/plugin.json` (`version` field)
  for every plugin under `plugins/`
- `.claude-plugin/marketplace.json` (matching `version` for every
  plugin entry)
- one git commit + one git tag (when the user opts in)

This skill does **not** write or maintain CHANGELOG files.
Release notes live on the GitHub release and in `git log`.

## Procedure

### 1. Parse arguments

Form: `<bump>` where bump ∈ `patch | minor | major`.

No plugin selection. Releases are unified: every plugin under
`plugins/` advances together. If you only want to ship one
plugin, that's a sign the unified-version policy is wrong for
this marketplace — raise it as a design change, don't simulate
it by skipping plugins.

### 2. Confirm clean tree

`git status --porcelain` must be empty. If not, stop and ask the
user to commit or stash. Releases on dirty trees produce noisy
diffs and ambiguous tags.

Confirm we're on the default branch (or warn if not).

### 3. Run validation

Invoke `/mol-plugin:check`. If the verdict is `FIX REQUIRED`,
stop. The user can override with explicit confirmation, but
default is to halt.

### 4. Compute the new version

- Read the current shared version from any `plugin.json`
  (they should all agree; if they don't, stop and tell the user
  to align them first — see § Drift detection).
- Bump per requested level (semver: `0.1.3` + patch → `0.1.4`,
  `0.1.3` + minor → `0.2.0`, `0.1.3` + major → `1.0.0`).
- Record old → new.

### 5. Drift detection

If any plugin's `plugin.json` has a different `version` from the
others (or different from its `marketplace.json` entry), stop.
Report which plugins are out of sync. Fixing drift is a
prerequisite of a unified release; the user either:

- aligns by hand and re-runs, or
- asks the skill to align first via a separate "drift fix" commit
  (then re-runs the release on the aligned tree).

This skill does not silently absorb drift, because doing so would
hide the question of *which* version is correct.

### 6. Reach approval

Show the user:

- old shared version → new shared version
- the proposed commit message (`release: v<new>`)
- the proposed tag (`v<new>`)
- the list of plugins being advanced (just for visibility — they
  all advance together)

Wait for go-ahead.

### 7. Apply

For every plugin under `plugins/`:

- write its `plugin.json` with the new version
- update its entry in `.claude-plugin/marketplace.json` with the
  same new version

Stage:

```
git add plugins/*/.claude-plugin/plugin.json
git add .claude-plugin/marketplace.json
```

Run the pre-commit gate by invoking `/mol:ship commit`. If the
verdict is **BLOCK**, stop and surface the blocker. The user has
already approved the bump in Step 6, so this skill provides its
own commit message ("release: v<new>") and does not delegate to
`/mol:commit` (which would re-prompt for message approval).

If the gate reports **PROCEED**, commit and tag:

```
git commit -m "release: v<new>"
git tag v<new>
```

One commit, one tag, regardless of how many plugins are in the
marketplace.

Do **not** push. The release commit and the tag stay local; the
publish phase is the user's next step (see § 8).

### 8. Report

One-line summary:
`released v0.1.1 → v0.1.2 (tag v0.1.2, N plugins advanced)`

Then print the **publish sequence**, in this order — both halves
matter, and the order is load-bearing:

```
Next steps to publish v<new>:

  1. /mol:push                 # push master to origin (your fork)
  2. /mol:pr                   # open PR origin → upstream/master
  3. (wait for PR to merge into upstream/master)
  4. /mol:tag                  # push the tag — refuses if step 3
                               # hasn't happened (orphan-tag guard)

Why both halves: the marketplace.json version bump lives in the
release *commit*. If you only push the tag, the release tarball
is correct, but marketplace.json on upstream's default branch
still shows the old version, so users browsing the registry see
the previous release. The branch-merge half is what makes the new
version visible; the tag-push half is what triggers the GitHub
Actions release workflow.
```

Single-remote layouts (no `upstream`) collapse steps 1–3 to a
single `git push` to the canonical repo's default branch, but the
two phases (branch then tag) still apply.

## Guardrails

- **Do not** push to a remote. Tagging and committing locally is
  the boundary.
- **Do not** force-overwrite an existing tag. If `v<new>` already
  exists, stop.
- **Do not** create or modify any CHANGELOG file. The marketplace
  policy is "no CHANGELOG; release notes belong on GitHub
  releases and in `git log`."
- **Do not** release if `/mol-plugin:check` reports `FIX
  REQUIRED` without explicit user override.
- **Do not** advance a subset of plugins. Unified versioning means
  all-or-nothing.

## Idempotency

Releasing the *same* version twice is an error: tag collision
stops the run. To redo a botched release, the user must delete
the tag manually (locally and remotely) and re-run; this skill
does not delete tags.

A run that reaches the approval gate and is rejected leaves the
tree exactly as it found it. No file writes happen before
approval.

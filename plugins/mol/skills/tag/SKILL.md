---
name: tag
description: Push an existing local release tag to upstream so the GitHub Actions release workflow fires. Use after `/mol-plugin:release` has cut the tag and `/mol:pr` has merged the version-bump commit to upstream's default branch; refuses orphan tags, overwrites, or pushing tags to origin.
argument-hint: "[<tag>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:tag — Push Release Tag to Upstream

`/mol-plugin:release` writes bumped `plugin.json` / `marketplace.json`, commits, creates local annotated tag `v<X.Y.Z>` — but deliberately does **not** push. This skill is the *tag-push* step: sends the tag (only the tag) to `upstream`, activating GitHub Actions `on: push: tags:` release workflow.

The fork (`origin`) is irrelevant here. Releases live on the canonical repo.

**Second half of publishing a release, not the whole thing.** The release commit carries the `marketplace.json` version bump and must reach `upstream`'s default branch first (via `/mol:push` + `/mol:pr` + merge), otherwise the tag is orphan: tarball-correct but registry-stale. Step 3 enforces this.

## Procedure

### 1. Resolve config

- `upstream` remote must exist. If absent:
  - `origin` points to a fork (GitHub repo has `parent`) → offer to add upstream automatically.
  - `origin` is the canonical repo (single-remote / solo-maintainer) → warn that `origin` will be the release target, ask explicit confirmation.
- Push target (`<release-remote>`) = `upstream` if exists, else `origin` after explicit confirmation.

### 2. Pick the tag

`$ARGUMENTS` non-empty → use it.

Otherwise, find most recent local tag **not** present on `<release-remote>`:

```
git fetch --tags <release-remote>
local_tags=$(git tag --sort=-creatordate)
remote_tags=$(git ls-remote --tags <release-remote> | awk '{print $2}' | sed 's|refs/tags/||;s|\^{}$||' | sort -u)
```

First local tag not in `remote_tags` is candidate. None → stop with "no unpushed tags — `/mol-plugin:release` first or pass an explicit tag name."

### 3. Verify the tag

- `git rev-parse "<tag>"` succeeds (tag exists locally).
- Tag's commit subject matches `^release: v` (convention `/mol-plugin:release` writes). If not, warn + ask explicit confirmation.
- Tag **not** already on `<release-remote>`. If it is, stop. Never overwrites; user must delete upstream tag manually first (`git push <release-remote> :refs/tags/<tag>`). Common reason: previous push left orphan tag pointing at pre-merge commit, then PR was squash/rebase-merged — see orphan-tag-guard recovery (path B).
- **Reachability (orphan-tag guard).** Tag's commit reachable from `<release-remote>`'s default branch. Resolve default branch as `<release-remote>/HEAD` (or fall back to `<release-remote>/master`/`main`):

  ```
  git fetch <release-remote>
  git merge-base --is-ancestor <tag>^{commit} <release-remote>/<default-branch>
  ```

  Check fails → **stop by default**. The release commit carries the `marketplace.json` / `plugin.json` version bump; pushing the tag while the commit is missing from default branch creates an *orphan tag* — GitHub release tarball is fine, but registry shows the previous version on the default branch.

  Tell user the recovery path explicitly:

  ```
  Tag <tag> points at <short-sha> which is not reachable from
  <release-remote>/<default-branch>.

  A. Branch hasn't been merged yet — publish it first.
       /mol:push      # release branch → origin (fork)
       /mol:pr        # PR origin → upstream
       (merge the PR; prefer *merge-commit* style — see B)
       /mol:tag <tag> # re-run

  B. Branch was squash-merged or rebase-merged. The merged commit
     on <release-remote>/<default-branch> has a different SHA
     than your local tag, so the local tag still points at the
     now-vanished pre-merge commit. Retag at the merged HEAD:

       git fetch <release-remote>
       git tag -d <tag>
       git tag <tag> <release-remote>/<default-branch>
       /mol:tag <tag> # re-run

     If <tag> was *also* pushed to <release-remote> while still
     pointing at the pre-merge SHA (orphan remote tag), delete
     the remote tag first (destructive — confirm intent):

       git push <release-remote> :refs/tags/<tag>

  C. Override (intentionally want an orphan tag — rare, e.g.
     cherry-picked hotfix pointing outside the default branch):
     re-run with explicit confirmation.
  ```

  Honor case C only after user types it explicitly.

### 4. Refuse `origin` when `upstream` exists

If `upstream` is configured and skill is asked to push to `origin`, refuse. Tags belong on the canonical repo. Single-remote (no `upstream`) handled by step 1's warn-and-confirm.

### 5. Reach approval

Show:

- Tag name.
- Commit it points to (short SHA + subject).
- Push destination: resolved URL of `<release-remote>` (so user sees *which* org).
- Reminder this push activates GitHub Actions release workflows.

Wait for explicit go-ahead.

### 6. Push the tag

```
git push <release-remote> <tag>
```

Tag *only*. No branches. No `--force` — step 3 already stopped if upstream ref exists.

### 7. Verify and report

```
git fetch --tags <release-remote>
git ls-remote --tags <release-remote> "<tag>"
```

Then emit the one-line F2 summary:

```
/mol:tag: pushed <tag> → <release-remote>
  commit:  <short-sha> <subject>

If a release workflow is configured (.github/workflows/*.yml with
'on: push: tags:'), it should trigger now. Check Actions for
status.
```

If no release workflow under `.github/workflows/` matching `on: push: tags`, mention explicitly so user knows the push alone won't produce a GitHub Release page.

## Guardrails

- **Never** push to `origin` when `upstream` exists.
- **Never** push branches from this skill — only the tag.
- **Never** force-push a tag (`--force` / `-f`).
- **Never** create a tag from this skill — only push existing tags. Creation is `/mol-plugin:release` (or `git tag` manually).
- **Never** run `git push --tags` (pushes *all* unpushed tags). Push exactly one explicit tag.
- **Never** push an orphan tag silently. Refuse by default at Step 3; surface publish-branch-first recovery. Override exists for genuine cherry-picked hotfix tags but must be typed by user.

## Idempotency

Pushing a tag that already exists on the release remote is refused at step 3, not silently re-pushed. Redo a botched release: delete upstream tag manually (`git push <release-remote> :refs/tags/<tag>`) and re-run.

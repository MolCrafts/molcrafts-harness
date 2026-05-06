---
description: Push an existing release tag to upstream (the canonical org-owned repo) so that GitHub Actions release workflows fire. Pairs with /mol-plugin:release (which creates the local tag) — this skill is the *tag-push* phase, not the cut phase. Follows the standard GitHub fork convention — origin = your fork, upstream = the canonical repo. Refuses to push tags to origin, refuses to overwrite an existing remote tag, and refuses to push a tag whose commit is not reachable from upstream's default branch (orphan-tag guard — the user must publish the branch via /mol:push + /mol:pr first, otherwise the marketplace.json version bump never reaches upstream/master and users see a stale version on the registry).
argument-hint: "[<tag>]"
---

# /mol:tag — Push Release Tag to Upstream

`/mol-plugin:release` writes the bumped `plugin.json` /
`marketplace.json`, commits, and creates a local annotated tag
`v<X.Y.Z>` — but it deliberately does **not** push. This skill is
the *tag-push* step: it sends the tag (and only the tag) to
`upstream`, which is what activates a GitHub Actions
`on: push: tags:` release workflow.

The fork (`origin`) is irrelevant here. Releases live on the
canonical repo.

**This skill is the second half of publishing a release, not the
whole thing.** The release commit carries the `marketplace.json`
version bump and must reach `upstream`'s default branch first
(via `/mol:push` + `/mol:pr` + merge), otherwise the tag is
orphan: tarball-correct but registry-stale. Step 3 enforces this
with a reachability check.

## Procedure

### 1. Resolve config

- `upstream` remote must exist. If absent:
  - If `origin` points to a fork (GitHub repo has a `parent`),
    offer to add upstream automatically.
  - If `origin` is itself the canonical repo (single-remote /
    solo-maintainer layout), warn the user that `origin` will be
    used as the release target, and ask for explicit confirmation.
    The fork/upstream separation that this skill protects isn't
    present, so the warn-and-confirm is the safety boundary.
- The push target (call it `<release-remote>`) is `upstream` if it
  exists, else `origin` after explicit confirmation.

### 2. Pick the tag

If `$ARGUMENTS` is non-empty, use it as the tag name.

Otherwise, find the most recent local tag that is **not** present
on `<release-remote>`:

```
git fetch --tags <release-remote>
local_tags=$(git tag --sort=-creatordate)
remote_tags=$(git ls-remote --tags <release-remote> | awk '{print $2}' | sed 's|refs/tags/||;s|\^{}$||' | sort -u)
```

The first local tag not in `remote_tags` is the candidate. If no
such tag exists, stop with "no unpushed tags — `/mol-plugin:release`
first or pass an explicit tag name."

### 3. Verify the tag

- `git rev-parse "<tag>"` succeeds (tag exists locally).
- The commit the tag points to has a subject matching `^release: v`
  (the convention `/mol-plugin:release` writes). If not, warn the
  user and ask for explicit confirmation — pushing a tag onto a
  non-release commit is a footgun for downstream release
  automation.
- The tag is **not** already on `<release-remote>`. If it is,
  stop. This skill never overwrites an existing remote tag; the
  user must delete the upstream tag manually first.
- **Reachability (orphan-tag guard).** The tag's commit is reachable
  from `<release-remote>`'s default branch. Resolve the default
  branch as `<release-remote>/HEAD` (or fall back to
  `<release-remote>/master`/`main`), then:

  ```
  git fetch <release-remote>
  git merge-base --is-ancestor <tag>^{commit} <release-remote>/<default-branch>
  ```

  If the check fails, **stop by default**. The release commit
  carries the `marketplace.json` / `plugin.json` version bump;
  pushing the tag while the commit is missing from the default
  branch creates an *orphan tag* — the GitHub release tarball will
  be fine, but users browsing the registry see the previous version
  on the default branch, which is exactly the inconsistency the
  publish flow is supposed to prevent.

  Tell the user the recovery path explicitly:

  ```
  Tag <tag> points at <short-sha> which is not on
  <release-remote>/<default-branch>. Publish the branch first:

    /mol:push      # master → origin (your fork)
    /mol:pr        # open PR origin → upstream
    (merge the PR)
    /mol:tag <tag> # re-run

  Override (only if you intentionally want an orphan tag — rare,
  e.g. cherry-picked hotfix tag): re-run with explicit
  confirmation.
  ```

  Honor an explicit override only after the user types it — do
  not auto-proceed on the first refusal.

### 4. Refuse `origin` when `upstream` exists

If `upstream` is configured and the user somehow asked the skill
to push to `origin` instead, refuse. Tags belong on the canonical
repo. Single-remote layouts (no `upstream`) are handled by step 1's
warn-and-confirm.

### 5. Reach approval

Show:

- Tag name.
- Commit it points to (short SHA + subject).
- Push destination: resolved URL of `<release-remote>` (so the
  user sees *which* org).
- A reminder that this push is what activates GitHub Actions
  release workflows (if any are configured).

Wait for explicit go-ahead.

### 6. Push the tag

```
git push <release-remote> <tag>
```

Push the tag *only*. Do not push branches. Do not pass `--force` —
if the upstream ref already exists, step 3 already stopped us.

### 7. Verify and report

Re-fetch tags and confirm the tag now exists on the upstream:

```
git fetch --tags <release-remote>
git ls-remote --tags <release-remote> "<tag>"
```

Then report:

```
/mol:tag: pushed <tag> → <release-remote>
  commit:  <short-sha> <subject>

If a release workflow is configured (.github/workflows/*.yml with
'on: push: tags:'), it should trigger now. Check Actions for
status.
```

If there is no release workflow under `.github/workflows/` matching
`on: push: tags`, mention that explicitly so the user knows the
push alone won't produce a GitHub Release page.

## Guardrails

- **Never** push to `origin` when `upstream` exists.
- **Never** push branches from this skill — only the tag.
- **Never** force-push a tag (`--force` / `-f`).
- **Never** create a tag from this skill — only push existing
  tags. Tag *creation* is `/mol-plugin:release` (or `git tag`
  manually).
- **Never** run `git push --tags` (pushes *all* unpushed tags).
  Push exactly one explicit tag.
- **Never** push an orphan tag silently. If the tag's commit is
  not reachable from `<release-remote>`'s default branch, refuse
  by default (Step 3) and surface the publish-branch-first
  recovery path. An override exists for genuine cherry-picked
  hotfix tags but must be typed by the user, not assumed.

## Idempotency

Pushing a tag that already exists on the release remote is refused
at step 3, not silently re-pushed. To redo a botched release, the
user must delete the upstream tag manually
(`git push <release-remote> :refs/tags/<tag>`) and re-run.

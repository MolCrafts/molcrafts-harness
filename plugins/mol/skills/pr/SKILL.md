---
name: pr
description: Open a pull request from origin (your fork) to upstream's default branch via the gh CLI, drafting title and body from the commit range. Use to ship a feature branch; calls `/mol:push` first (which gates on `/mol:ship` and pushes to origin).
argument-hint: "[<title>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:pr — Pull Request from Fork to Upstream

Creates a GitHub PR. Base = `upstream` / `<default_branch>`; head = `origin` (fork). Direct upstream pushes out of scope — fork branch reaches upstream only via "PR + review."

## Procedure

### 1. Resolve config

- **Origin** must exist (`git remote get-url origin`). Else stop.
- **Upstream**: `git remote get-url upstream`.
  - Absent + `origin` is a fork (GitHub `parent` field set) → offer to add: `git remote add upstream <parent-url>`.
  - Absent + `origin` not a fork → cannot proceed; stop and tell user.
- **Branch**: `git rev-parse --abbrev-ref HEAD`.

Resolve upstream default branch:

```
git fetch upstream
git symbolic-ref --short refs/remotes/upstream/HEAD 2>/dev/null \
  | sed 's@^upstream/@@'
```

Fallback: `git ls-remote --heads upstream main master | head -1`.

Current branch == default branch → stop. PR `master`-fork → `master`-upstream is rarely intent; ask user to create a feature branch.

### 2. Verify gh is installed and authenticated

`gh auth status`. Unauthenticated → stop, tell user to run `gh auth login` (interactive).

### 3. Push first

Invoke `/mol:push`. It runs `/mol:commit` if dirty (which gates on `/mol:ship commit`), then `/mol:ship push`, then `git push origin`. `/mol:push` blocker → stop.

### 4. Draft title and body

Compare range: `upstream/<default_branch>..HEAD`.

`$ARGUMENTS` non-empty → treat as PR title.

Else:

- **Title** — one commit in range → its subject (≤ 70 chars; truncate with `…`). Multiple → pick dominant theme by reading subjects, prefix conventional-commit type, write a one-line summary.
- **Body** — standard format:

  ```
  ## Summary
  - <bullet 1>
  - <bullet 2>

  ## Test plan
  - [ ] <what was tested locally>
  - [ ] <regression risk to verify>
  ```

  Bullets explain **why**, not restate diff. Read commits + actual diff; do not just copy commit subjects.

Show title + body. Wait for approval. User may edit either inline.

### 5. Detect existing PR

```
gh pr view --json url,state 2>/dev/null
```

PR exists for this branch and is `OPEN` → **do not create**. Report URL and stop. `CLOSED` / `MERGED` → ask whether to open new or revive.

### 6. Create the PR

```
gh pr create \
  --base "<default_branch>" \
  --repo "<upstream-owner>/<upstream-repo>" \
  --title "<title>" \
  --body "$(cat <<'EOF'
<body>
EOF
)"
```

`<upstream-owner>/<upstream-repo>` from parsing the `upstream` remote URL. Head auto-resolved by `gh` from branch's tracking remote (`/mol:push` set with `-u` on `origin`).

`gh pr create` errors → surface verbatim.

### 7. Report

```
/mol:pr: opened PR <number> against upstream/<default_branch>
  <url>
```

## Guardrails

- **Never** create PR with default branch as head.
- **Never** open PR without going through `/mol:push`.
- **Never** `--draft` automatically — user decides on approval gate.
- **Never** assign reviewers / add labels automatically.

## Idempotency

Re-run on a branch with an open PR is a no-op (reports existing URL). After existing PR merges/closes, a new run can open a new PR.

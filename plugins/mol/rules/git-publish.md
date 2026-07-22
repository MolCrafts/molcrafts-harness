# Git publish chain — remotes, pre-commit, PR-first

Canonical rules for `/mol:commit`, `/mol:push`, `/mol:pr`, `/mol:release`,
`/mol-plugin:release`, and `/mol:tag`. Skills implement procedure; this
file owns the invariants. Do not restate conflicting remote or merge
policy inside a skill.

## Remotes (fork pair)

MolCrafts packages almost always use a **paired remote layout**:

| Remote | Role | What may go there |
|---|---|---|
| **`origin`** | Developer's **fork** | Branch pushes only (`/mol:push`) |
| **`upstream`** | Canonical MolCrafts repo | **No branch pushes.** Land via PR + merge. Tags only after merge (`/mol:tag`) |

If `upstream` is missing and `origin` is a GitHub fork, add it from the
parent URL automatically. If there is no fork pair (single remote that
*is* the canonical repo), branch push to that remote is allowed for
solo/private work — still never skip pre-commit / ship gates.

## Iron law A — pre-commit ≡ CI

Local hooks must mirror remote CI so failures are caught **before** any
network push (fork or otherwise). Red Actions on the org repo spam
watchers with email; local parity is the primary defense.

1. `.pre-commit-config.yaml` exists (else `/mol:ci-sync`; still missing → **BLOCK**).
2. Hooks installed (`pre-commit install` best-effort).
3. No `CI_ONLY` drift (CI check absent from pre-commit) → `/mol:ci-sync` then re-run.
4. Before push: `pre-commit run --all-files` (full tree, not staged-only) **and** `/mol:ship push`.
5. Prefer fixing over bypass. `--no-verify` only on `/mol:push` after **explicit** user consent; forbidden on default/release branches; never invented by the agent.

Commit tier runs the fast subset (hooks on staged files + `/mol:ship commit`).
Push tier is the full local CI-equivalent wall.

## Iron law B — PR-first landing (never direct-push to upstream)

To put commits on the **canonical** default branch:

```
/mol:commit  →  /mol:push (origin only)  →  /mol:pr  →  merge PR  →  [/mol:tag]
```

| Forbidden | Required instead |
|---|---|
| `git push upstream <branch>` (any branch) | `/mol:pr` (after `/mol:push`) |
| `git push` that updates `upstream`'s default | Open PR → green checks → merge |
| Force-push to any shared remote | Rebase/fix locally; never `--force` / `--force-with-lease` from these skills |
| Push release branch straight to org `main` | `release/v*` on origin → PR → merge → tag |

**Why:** Direct pushes to the org default branch run Actions on the
canonical repo. Failures email everyone watching. PR CI runs against the
head first; only green work merges, so the org default stays green.

## Skill roles (one chain, no shortcuts)

| Skill | Mutates | Remote |
|---|---|---|
| `/mol:commit` | Local commit only | — |
| `/mol:push` | Branch tip | **`origin` only** |
| `/mol:pr` | Opens GitHub PR | head=`origin`, base=`upstream/<default>` |
| `/mol:release` / `/mol-plugin:release` | Version + full chain | commit → push → pr → **wait checks** → merge → tag |
| `/mol:tag` | Annotated tag object already local | Tag ref to **`upstream`** (or sole remote) — never orphan tags |

## Merge policy (after PR)

1. **Never** merge a red PR. Wait for required checks (`gh pr checks
   --watch` or equivalent) until green or a hard timeout → **BLOCK** and
   report failures (route `/mol:fix` / re-push).
2. Prefer merge **without** `--admin` so branch protection is honored.
3. Use `--admin` only when the merge is blocked solely by permissions /
   admin-only protection **and** checks are already green — never to
   override failing CI.
4. Prefer merge commit for release branches (stable tag SHA). Retag at
   upstream tip only if squash rewrote the commit.

## Idempotency

- Branch already on origin at same SHA + green gates → push no-op.
- Open PR already exists for the head → pr reports URL, no-op.
- Version + tag already on upstream → release no-op.
- Tag already on release remote at same SHA → tag no-op.

## Anti-patterns

- Treating `origin` as the org repo when a fork pair exists.
- "Just push this fix to upstream main" — always PR.
- Skipping `/mol:ci-sync` when CI and pre-commit diverge.
- Merging with `--admin` while checks are red or pending.
- Pushing tags before the release commit is on the upstream default
  (orphan tags — `/mol:tag` must refuse).

---
name: ship
description: Pre-commit / pre-push / pre-merge CI-parity gate. Runs a tiered set of checks (format, lint, tests, full CI equivalent) and reports PROCEED or BLOCK. Never writes code.
argument-hint: "<commit | push | merge>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:ship — CI Parity Gate

Read CLAUDE.md → parse `mol_project:` (`$META`).

**Read-only.** Does not edit code, write tests, or run state-changing git. Executes pre-flight checks + reports PROCEED or BLOCK.

## Tier selection

First positional arg selects the gate. Cumulative — `merge` ⊇ `push` ⊇ `commit`.

- `commit` — format + lint + **project pre-commit hooks** (must mirror CI). Before every `git commit`. Fast (~60s).
- `push` — full pre-commit `--all-files` + full test suite. Before every `/mol:push` (origin/fork only — see `../../rules/git-publish.md`). Medium (5–10 min). **Iron law:** hooks installed, pre-commit ≡ CI, green — or user-explicit `--no-verify` only.
- `merge` — mirrors remote CI locally. Before merge to `main`/`master`. Heavy (full CI wall-clock).

`$ARGUMENTS` empty → default to `commit` and state the assumption.

## Procedure

1. **Resolve tier** from `$ARGUMENTS`.

2. **Pre-commit presence (commit/push tiers).** If `.pre-commit-config.yaml` is missing → report 🚨 Critical `PRECOMMIT_MISSING` and **BLOCK**. If present but hooks not installed → 🚨 `PRECOMMIT_NOT_INSTALLED`. If CI has checks absent from pre-commit → 🚨 `CI_ONLY` drift (route `/mol:ci-sync`).

3. **Delegate to `ci-guard` agent** with tier as input. Agent detects CI config, runs tier's commands (including `pre-commit run --all-files` on push when available), interprets failures, reports CI-only drift modes (platform, matrix, secrets, cache, services).

4. **Aggregate** findings into severity table:

   | 🚨 Critical | 🔴 High | 🟡 Medium | 🟢 Low |
   |-------------|---------|-----------|--------|
   | N           | N       | N         | N      |

5. **Decide verdict** from tier + findings:

   - `commit` + any 🚨 → **BLOCK COMMIT**
   - `push` + any 🚨 → **BLOCK PUSH**
   - `merge` + any 🚨 or 🔴 → **BLOCK MERGE**
   - No blocker at requested tier → **PROCEED**
   - 🟡 / 🟢 informational; never block.

6. **Route fixes.** For each blocker, name the `/mol:*` skill (this skill refuses to edit):

   - lint / format → `/mol:fix <file>` with failing rule
   - failing test → `/mol:fix` (expected to pass) or `/mol:impl` (feature incomplete)
   - architecture violation surfaced by CI → `/mol:review --axis=arch` then `/mol:refactor`
   - doc drift → `/mol:docs`
   - CI-config drift (matrix / secrets / runner) → ask user to update `$META.ci` or workflow file. Never edit workflows automatically.

7. **Never auto-fix.** Refuses to edit even when fix is trivial. Callers (`/mol:push`, `/mol:commit`) own the fix loop. This skill only reports PROCEED/BLOCK.

Missing pre-commit or CI_ONLY drift is always a push-tier 🚨.

## Output

```
Gate: <tier>
Verdict: PROCEED | BLOCK

(severity table)

(ci-guard findings verbatim, severity-sorted)

Next steps:
- <action 1>
- <action 2>
```

End with one-line summary:

```
/mol:ship <tier>: PROCEED (N findings, none blocking)
```

or

```
/mol:ship <tier>: BLOCK — <top blocker in one phrase>
```

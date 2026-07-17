---
name: push
description: Push the current branch to origin after CI-parity pre-commit + /mol:ship push. Ensures pre-commit is installed and mirrors CI, auto-fixes failures in a loop, never force-pushes. Only offers --no-verify after fix attempts fail and the user explicitly accepts. Auto-invoked by /mol:pr, /mol:release, and /mol-plugin:release.
argument-hint: "[<branch>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:push — Gated Push to Fork

Writes to a remote: `git push origin`. Standard GitHub fork-and-PR layout:

- **`origin`** = contributor's personal fork. Feature / release branches push here.
- **`upstream`** (when present) = canonical org-owned repo. Branches **never** push here from this skill — reach upstream only via `/mol:pr` (+ merge).

**Fully agent-driven** for mechanical steps — except the optional `--no-verify` escape hatch, which **requires explicit user consent**.

---

## Iron law — pre-commit ≡ CI (must pass before push)

Every push is blocked until local hooks that mirror remote CI are green.
This is non-negotiable. CI failures that pre-commit would have caught are a
`/mol:push` contract violation.

### Step 0 — Ensure CI-parity pre-commit exists and is installed

1. **Config present.** Root has `.pre-commit-config.yaml`.
   - Missing → invoke `/mol:ci-sync` (scaffold + parity with CI workflow /
     `$META.build` / `$META.ci`). Still missing after → **BLOCK PUSH**.
2. **pre-commit binary + hooks.**

   ```
   pre-commit --version          # must exist on PATH
   pre-commit install            # best-effort; may fail if core.hooksPath is set
   ```

   Missing binary → install (`pipx install pre-commit` / project venv).
   If `pre-commit install` fails because `core.hooksPath` is set (common with
   shared hook managers), **do not stop** — agent must still run
   `pre-commit run --all-files` explicitly before every push (this skill
   enforces the gate even when git will not fire the hook).
3. **Parity check (cheap).** Diff hook commands against the CI workflow
   (`.github/workflows/*` or `$META.ci`). Any CI check not represented in
   pre-commit → invoke `/mol:ci-sync` to patch, then re-run. Do not push
   with known `CI_ONLY` drift.
4. **Run the full local gate.**

   ```
   pre-commit run --all-files
   ```

   Prefer this over a partial staged-only run before push — catch what CI will.

### Step 0b — Fix loop (agent-driven)

On failure:

1. Parse failing hook output.
2. Fix in-loop when mechanical (format, lint auto-fix, test assertion drift
   from intentional product change, missing files). Use `/mol:fix` /
   `/mol:simplify` / direct edit as appropriate.
3. Re-run `pre-commit run --all-files`.
4. Repeat up to **3** full fix cycles.

Still red after 3 cycles, or volume is clearly beyond this session
(dozens of unrelated failures, missing env, flaky external service):

```
BLOCK PUSH — pre-commit still failing after N fix attempts.

Failures:
  - <hook>: <one-line reason>
  - …

Options (you must choose — agent will not decide alone):
  1. Keep fixing (agent continues next cycle with more context you provide)
  2. Push with --no-verify  (LAST RESORT — CI will almost certainly fail;
     only for emergency WIP on a non-default branch you own)
  3. Abort push
```

- **Never** pass `--no-verify` unless the user explicitly chose option 2
  in this turn (literal confirmation: `yes --no-verify` / `用 --no-verify`).
- Default branch / release branch → **refuse** `--no-verify` even if asked;
  fix or abort only.
- After an allowed `--no-verify` push, report loudly that CI is expected to
  fail and list the remaining failures.

Also invoke `/mol:ship push` (full test suite / merge-tier extras when
configured). pre-commit is necessary but not always sufficient; ship covers
long suite items left out of commit-stage hooks.

---

## Procedure

### 1. Resolve branch and remote

- Branch: `$ARGUMENTS` if provided, else current (`git rev-parse --abbrev-ref HEAD`).
- Push target = `origin`. Missing → stop hard.

Single-remote (no `upstream`) → push to `origin` without asking.

### 2. Default-branch guard (forks only)

`upstream` exists and current branch == upstream default → **stop hard** (do not push default from a fork). Create/switch to a feature or release branch instead — no user prompt, report the stop.

No `upstream` → skip.

### 3. Commit pending work first

`git status --porcelain` non-empty → invoke `/mol:commit` (no prompt; commit
itself runs pre-commit hooks via git). BLOCK → stop (same fix loop as § 0b
if the failure is hook-related).

Clean tree → skip.

### 4. Pre-commit iron law + ship gate

1. Execute **Iron law** § 0 + § 0b until green (or user-accepted `--no-verify`).
2. Invoke `/mol:ship push`.
   - **BLOCK** → enter fix loop (same 3-cycle budget, cumulative with § 0b).
   - **PROCEED** → continue.

### 5. Push

```
git push -u origin <branch>
```

Only if the user explicitly accepted `--no-verify` under § 0b:

```
git push -u origin <branch> --no-verify
```

Never `--force` / `--force-with-lease`.

### 6. Report

```
/mol:push: pushed <branch> → origin/<branch>
  <short-sha-range>
  pre-commit: green | BYPASSED (--no-verify, user-approved)
```

## Guardrails

- **Iron law:** no green pre-commit (or explicit user `--no-verify`) → no push.
- **Never** skip pre-commit install / parity repair silently.
- **Never** invent `--no-verify` without the user's explicit choice this turn.
- **Never** `--no-verify` to default/release branches.
- **Never** push to `upstream`.
- **Never** force-push.
- **Never** push tags — `/mol:tag` only.
- Prefer fixing over bypassing. Bypass is a loud, rare exception.

## Idempotency

Up-to-date branch + green hooks → no-op success.

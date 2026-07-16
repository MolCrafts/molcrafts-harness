---
name: close
description: Advance a code-complete spec to done and delete it. Fully agent-driven — auto-runs owed evaluators, re-checks the ledger, and when no evaluator can run asserts remaining pending criteria with verified_by agent-auto. Never asks the operator to close a spec. Auto-invoked by /mol:impl and /mol:impl-all.
argument-hint: "<spec-slug> [--manual]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:close — Spec Closer

The closing counterpart to `/mol:impl`. Finishes parked specs: re-checks the ledger, advances to `done`, deletes artifacts.

**Never leave closing to the human.** Auto-invoked by `/mol:impl` § 4d and `/mol:impl-all`. Standalone runs are also fully agent-driven.

`--manual` remains as an explicit override flag (same effect as agent-auto attestation) for rare operator re-runs; default mode already self-attests when evaluators cannot run.

## 1. Pre-flight

Read `CLAUDE.md` → parse `mol_project:` (`$META`); else emit adoption hint and stop.

Resolve `<slug>` → spec + acceptance. Refuse if missing.

**Status gate:**

- `draft` / `approved` / `in-progress` → refuse (implement first).
- `code-complete` → proceed.
- `done` → no-op success (spec should already be deleted; warn if file still present).

Categorise criteria:

- **A** = already `verified`
- **B** = `pending` re-checkable here (`code` / `runtime` with runnable `pass_when`)
- **C** = `pending` needing evaluator or attestation (`scientific` / `performance` / `docs` / legacy `ui_runtime`)

## 2. Re-check B

For each **B**: evaluate `pass_when`. Pass → `verified`. Fail → `failed` and **abort** (broken; run `/mol:fix`, do not advance).

## 3. Clear C without asking

If **C** empty → § 5.

Otherwise, **agent-driven clearance** (no user menu):

1. Group **C** by owed evaluator (`plugins/mol/rules/evaluator-protocol.md`).
2. Auto-invoke each available evaluator once:
   - `scientific` / `performance` → `/mol:bench <slug>` when `mol_project.bench.repo` is set
   - UI checks → `/mol:web <slug>` when Playwright MCP / dev config available
   - `docs` → run a best-effort docs presence check (paths exist / docstrings present); flip when objectively met
3. Re-read acceptance. Remaining **C**:
   - Flip each to `verified` with `verified_by: agent-auto` and `last_checked: <today>` plus a one-line note of what was checked or why attestation was used (e.g. `bench.repo unset`).
4. Never print "options for the operator". Never stop for `--manual` confirmation.

## 4. `--manual` flag

Same as agent-auto attestation for remaining **C**, with `verified_by: human` if the flag was literally passed. Prefer default mode (agent-auto) for all automatic callers.

## 5. Advance to done + delete

When every criterion is `verified`:

1. Spec frontmatter `status: done`, `last-updated: today`.
2. Invoke `/mol:commit` with message:

   ```
   chore(<scope>): close <slug> — <N> criteria verified
   ```

3. Delete spec, acceptance, INDEX entry, artifacts dir.
4. Stage deletions and amend into the close commit (atomic).

`/mol:commit` BLOCK → do not delete; revert status flip; stop hard with gate failure.

## 6. Output

```
[mol:close] <slug> — N criteria verified (B re-check, C agent-auto/evaluator), deleted in <sha>
```

## Guardrails

- **Refuse to close from `approved` / `in-progress`.**
- **Never ask the user to close or choose evaluators.**
- **No source code changes.**
- **Atomic commit + delete.**

---
description: Minimal-diff bug fix — reproduce, diagnose, patch the smallest surface, verify. Writes code.
argument-hint: "<bug description, error message, or failing test>"
---

# /mol:fix — Quick Fix

Read CLAUDE.md → parse `mol_project:` (`$META`). Read `$META.stage` (default `experimental`). Print `[mol] stage: <value>`.

`/mol:fix` is the **only** writing skill that proceeds at every stage — bugs are always in scope. Stage tightens scope discipline at Step 3 per `plugins/mol/rules/stage-policy.md`:

- `maintenance` — patch may not touch lines unrelated to reproduction; no new abstractions; no rename of any symbol (even local) outside immediate fix surface.
- `stable` — additive only by default; modifying existing public signature requires deprecation shim or explicit user approval.
- `beta` / `experimental` — standard scope discipline (smallest change that resolves issue).

## Procedure

1. **Reproduce.** Run `$META.build.check` + `$META.build.test` (or single-test form if failure is a specific test). Confirm reported symptom.

2. **Diagnose.** If the conversation or `$ARGUMENTS` already contains a debugger report (a block with **Root cause** / **Fix recommendation** / **Preventive measure** — e.g. from a prior `/mol:debug`), consume it directly — do **not** re-delegate. Otherwise delegate to `debugger` agent with symptom from `$ARGUMENTS`; it classifies (build / test / runtime), gathers evidence, returns that structured report. Use the report as the plan for Step 3 — do **not** re-derive diagnosis here. Report has `Open questions` → surface them and stop; user has more evidence to gather before fix is justified.

3. **Fix.** Delegate the patch to `implementer` agent: the debugger report as plan, the reproduction from Step 1 (or the regression test below) as the RED test, the smallest fix surface as scope — stage discipline above bounds that scope.
   - Touches architecture boundaries → consult `$META.arch.rules_section` in CLAUDE.md first and pass it as the layer constraint.
   - Root cause suggests missing test → delegate to `tester` agent for a regression test BEFORE the patch (RED), then `implementer` (GREEN).
   - **Type safety.** No escape-hatch top types (`any` / `Any` / `interface{}` / `dyn Any`); no dropping existing annotations. `implementer` enforces this; the Step 4 gate verifies. Exception: deserialization at system boundary, narrowed immediately.

4. **Verify.** Full `$META.build.test` (no regressions) + `$META.build.check` (format/lint).

5. **Report.** One-line summary: root cause, files changed, test added (if any).

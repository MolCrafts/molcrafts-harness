---
name: refactor
description: Restructure code while preserving all architectural invariants. Snapshot → incremental change → re-verify. Writes code.
argument-hint: "<what to refactor and why>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:refactor — Refactor

Read CLAUDE.md → parse `mol_project:` (`$META`). Read `$META.stage` (default `experimental`). Print `[mol] stage: <value>`.

## Stage gate (per `plugins/mol/rules/stage-policy.md`)

Apply before any other step:

- `maintenance` — **refuse**. Print: *"`<project>` is in `maintenance`; refactors are out of scope. Bump the stage in CLAUDE.md if intentional."* Stop.
- `stable` — proceed; public symbol renames require `pm` agent pre-review (delegate at Step 3 alongside `architect`). Internal renames unaffected.
- `beta` — proceed; Step 5 post-refactor `architect` check additionally verifies README / tutorial code blocks still parse against new public shape.
- `experimental` — full latitude; Step 1 snapshot records *current* shape; Step 5 public-API preservation clause is informational, not binding.

## Procedure

1. **Snapshot invariants.** Before any change:
   ```
   $META.build.check
   $META.build.test
   ```
   Record passing test list + public API surface to restructure (function signatures, exported symbols, module layout). Snapshot is what the refactor must preserve.

2. **Understand scope.** What moves where / gets renamed / merges / splits? What interfaces change? What stays the same?

3. **Architecture pre-check.** Delegate to `architect` agent on current state. Confirms current structure understood + target structure satisfies `$META.arch.rules_section`.

4. **Execute incrementally.** One logical change at a time. After each, run `$META.build.test`. If a change breaks more than expected tests → stop and investigate before continuing.

   **Type safety.** Refactor may only tighten types, never loosen — must not introduce `any` / `Any` / `interface{}` / `dyn Any`, must not strip existing annotations. Surfaced loose type = refactor opportunity to narrow it. Static type checker green at every step.

5. **Verify invariants.**
   - Same tests pass (no regressions).
   - Public API surface matches snapshot (unless user accepted API change in step 2).
   - Delegate to `architect` agent again for post-refactor compliance.

End with one-line summary: files moved/renamed, tests passing, API changes (if any).

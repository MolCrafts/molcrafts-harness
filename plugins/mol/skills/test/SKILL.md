---
name: test
description: Run the project's test suite and analyze test quality, coverage gaps, and missing categories.
argument-hint: "[module or test path]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:test — Test & Coverage Analysis

Read CLAUDE.md → parse `mol_project:` (`$META`).

## Procedure

1. **Run the suite.**
   - `$ARGUMENTS` given → prefer `$META.build.test_single` with `{path}` substituted. Else run `$META.build.test`.
   - Capture pass / fail / skip counts + failing test list.

2. **Delegate to `tester` agent in analyze-mode** for test-quality analysis (read-only; `/mol:impl` and `/mol:fix` are write-mode entry points). Agent inspects:
   - Documented test categories present (happy path, edge cases, immutability if project documents immutable flow, domain validation if `$META.science.required`)?
   - Tests deterministic (seeded, no time-of-day dependency)?
   - Assertions use appropriate tolerances for floating-point?

3. **Check coverage.** `$META.build.coverage` defined → run + summarize by module. Flag modules below project's documented target (CLAUDE.md target if stated, else 80%).

## Output

- Pass / fail / skip counts
- Per-module coverage (if coverage step ran)
- Missing test categories (from `tester` agent)
- Failing tests grouped by likely root cause (classification only — fixing is `/mol:fix`)

End with one-line summary.

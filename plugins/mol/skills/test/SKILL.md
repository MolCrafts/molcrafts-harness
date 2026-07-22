---
name: test
description: "Run suite + analyze-mode tester audit (layout/naming/single-function/hard-coded regressions). Free-form: 跑测试/覆盖/test quality. Read-only; writes go via /mol:impl or /mol:fix."
argument-hint: "[module or test path]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:test — Test & Coverage Analysis

Read CLAUDE.md → parse `mol_project:` (`$META`).

1. **Run** — `$META.build.test_single` if path in args, else `$META.build.test`. Capture pass/fail/skip + failures.
2. **Analyze** — `tester` analyze-mode (`agents/tester.md`: layout mirror, `TestFooClass`, no e2e under `tests/`, hard-coded regressions, determinism, tolerances, categories).
3. **Coverage** — if `$META.build.coverage` set, flag modules below CLAUDE target (else 80%).

Output: counts; coverage; layout/naming/e2e/third-party findings; missing categories; failure classification only (`/mol:fix` fixes). One-line summary.

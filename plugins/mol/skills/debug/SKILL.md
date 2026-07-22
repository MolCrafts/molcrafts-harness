---
name: debug
description: "Diagnose-only (read-only) root cause for build/test/runtime failures. Free-form: 为啥挂/先诊断/don't patch yet. Then /mol:fix to apply."
argument-hint: "<error message or symptom>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:debug — Diagnosis Only

Read CLAUDE.md → parse `mol_project:` (`$META`).

**Never edits files.** Diagnosis only. To patch, hand report to `/mol:fix`.

## Procedure

Delegate entire diagnosis to `debugger` agent with `$ARGUMENTS` as failure symptom. Agent classifies (build / test / runtime), runs `$META.build.*` to gather evidence, returns:

- **Classification.**
- **Root cause** — one paragraph, file:line precise.
- **Fix recommendation** — what to change, not the change.
- **Preventive measure** — test category + assertion shape that catches a regression.
- (when evidence inconclusive) **Open questions** — specific evidence user should gather before re-invoking.

Render agent output verbatim. Do not re-summarize — agent's structured report is the contract `/mol:fix` reads.

End with the one-line F2 summary: *"diagnosis only — invoke `/mol:fix <bug>` to apply; it consumes the report above without re-running diagnosis."*

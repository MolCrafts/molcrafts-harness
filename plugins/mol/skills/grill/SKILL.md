---
name: grill
description: Relentless plan interview (user-only entry). Stress-tests a plan you already have by running `/mol:grilling`.
disable-model-invocation: true
argument-hint: "<the plan or design to stress-test>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:grill — Plan Interrogation (user entry)

User-only entry for grilling. Other skills and free-form model triggers must call `/mol:grilling` directly — this skill is not reachable via model invocation (Claude `disable-model-invocation: true`; Codex `allow_implicit_invocation: false`).

## Procedure

1. Read sibling `../grilling/SKILL.md` completely (and `../CODEX.md` when on Codex).
2. Run a `/mol:grilling` session in **plan** mode with `$ARGUMENTS` as the plan under test.
3. Follow `/mol:grilling` end-to-end — do not re-implement the interview here.

## Guardrails

- **Thin entry only.** All interview rules live in `/mol:grilling`.
- **Do not** claim a different procedure than `/mol:grilling` plan mode.

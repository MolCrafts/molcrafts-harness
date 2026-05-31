---
description: Batch-implement a chain of specs from start to finish. Given a spec prefix, discovers all matching specs in `.claude/specs/` sorted by numeric suffix, then drives the chain itself — running `/mol:impl` + `/mol:commit` per spec in order. After each spec a cheap-model evaluator subagent independently confirms the terminal state and acceptance ledger before the chain advances. All gating, TDD, simplify, and verdict logic lives in `/mol:impl`. Never stops to ask questions.
argument-hint: "<spec-prefix>"
---

# /mol:impl-all — Batch Spec Chain Driver

Drive an entire spec chain (`<base>-01-<phase>`, `<base>-02-<phase>`, …) by iterating `/mol:impl` on each spec in order, committing between specs. All gating, testing, simplifying, and status advancement is `/mol:impl`'s job — this skill only discovers the chain, keeps it moving, and independently verifies each step before advancing.

```
/mol:impl-all morse-bond
→ finds morse-bond-01-potential, morse-bond-02-gradient, morse-bond-03-optimization
→ /mol:impl 01 → evaluator → /mol:commit → /mol:impl 02 → evaluator → /mol:commit → …
→ reports chain verdict
```

**Never asks questions.** Fully autonomous — the skill drives the chain inside its own agentic loop (invoking `/mol:impl` and `/mol:commit` via the Skill tool). It does **not** rely on Claude Code's `/goal` built-in: `/goal` is user-invoked only and cannot be triggered programmatically by a skill.

---

## Procedure

### 1. Discover the chain

Read `CLAUDE.md` → parse `mol_project:` (`$META`); else emit adoption hint and stop.

Scan `$META.specs_path` (default `.claude/specs/`) for files matching `<prefix>-<NN>-<phase>.md` where `<NN>` is a two-digit number. Include a bare `<prefix>.md` at position 00 if present. Sort ascending by `<NN>`.

At least 1 spec must exist. If none: *"no specs matching '<prefix>' found"* and stop.

Print the chain:

```
[mol:impl-all] chain: morse-bond (3 specs)
  01-potential      status: approved
  02-gradient       status: approved
  03-optimization   status: approved
```

Any spec with `status: draft` → refuse and stop (*"approve draft specs first: <list>"*). Any spec already at `done` or `code-complete` is listed in the table but skipped during the drive (already terminal).

### 2. Drive the chain

For each spec, in sorted order (skip ones already terminal):

```
═══ [mol:impl-all] 2/3: morse-bond-02-gradient ═══
```

**2a. Implement.** Invoke `/mol:impl <slug>` via the Skill tool. `/mol:impl` owns all guardrails (stage gate, science gate, scope classification, TDD, simplify, acceptance criteria, status advancement). Do not duplicate them here.

**2b. Evaluate (independent check — the `/goal` analogue).** After `/mol:impl` exits, do **not** trust its self-report. Dispatch a lightweight evaluator subagent on the cheapest available model (Haiku class) via the Agent tool. This mirrors what `/goal` does between turns — a fast, independent model confirms the completion condition — except scoped per spec instead of per turn. The evaluator is **read-only**; it never edits specs, acceptance files, or code.

Give the evaluator exactly this job:

```
Inspect spec "<slug>" and return its true terminal state. Read only.

  Spec file:        {specs_path}<slug>.md
  Acceptance file:  {specs_path}<slug>.acceptance.md

1. If the spec file is ABSENT → terminal_state = "done"
   (`/mol:impl` deletes a spec on advance to done). Return immediately.
2. Else read the spec frontmatter `status:` and the acceptance
   `criteria:` list (each has `id`, `type`, `status` ∈
   {pending, verified, failed}).
3. Classify:
   - any criterion `status: failed`            → terminal_state = "stalled"
   - spec `status` ∈ {approved, in-progress}   → terminal_state = "stalled"
   - spec `status: code-complete` AND ≥1 criterion still `pending`
                                                → terminal_state = "code-complete"
   - spec `status: code-complete` AND every criterion `verified`
                                                → terminal_state = "anomaly"
                                                  (should have advanced to done)

Return strictly this shape:
  terminal_state: done | code-complete | stalled | anomaly
  verified_count: <int>
  pending_count:  <int>
  pending:        [ { id, type, owed_evaluator } ]   # owed_evaluator per the
                  # type → evaluator map: performance/scientific → /mol:bench,
                  # ui_runtime → /mol:web, docs → human, code/runtime → re-run /mol:impl
  reason:         <one line>
```

**2c. Act on the verdict:**

- `done` → `/mol:commit -m "feat(<base>): implement <phase> (<NN>/<total>)"`, then next spec.
- `code-complete` → `/mol:commit` with whatever message `/mol:impl` parked it under; record the `owed_evaluator` set from the evaluator's `pending` list; then next spec.
- `stalled` → **stop the chain.** `/mol:impl` hit a blocker; later specs may depend on this one. Do not commit, do not skip ahead.
- `anomaly` → **stop the chain.** A `code-complete` spec whose criteria are all `verified` should have self-advanced to `done`; this is a `/mol:impl` discrepancy worth surfacing rather than committing over.

### 3. Report

Show one row per spec with its terminal status, using the evaluator's verdict (not the main-loop self-report). For every spec at `code-complete`, attribute the parking reason to the specific evaluator the subagent named, so the operator knows what to run next (or whether `/mol:close --manual` is appropriate).

```
═══ [mol:impl-all] chain verdict ═══

  morse-bond-01-potential      done
  morse-bond-02-gradient       done
  morse-bond-03-optimization   code-complete   owes: /mol:bench  (2 perf criteria)

  2 done, 1 parked, 0 failed
```

After the table, if any spec parked, print the chain-level **closing recipe** once (don't repeat per spec):

```
PARKED specs require runtime-evaluator verification before they
self-delete. To finish closing the chain:

  - Run each owed evaluator on its spec (e.g. `/mol:bench
    morse-bond-03-optimization`); evaluators flip their criteria to
    status: verified.
  - Re-run `/mol:impl <slug>` per spec — when every criterion is
    verified, the spec advances to done and is deleted.

Manual close (when no evaluator is available, e.g. mol_project.bench.repo
is unset):

  /mol:close <slug> --manual

  for each parked spec. Operator asserts the pass_when conditions
  are met; the audit trail lands in the commit message.
```

Skip the recipe entirely if no spec parked (chain reached `done` end-to-end).

End-of-skill one-line summary: `/mol:impl-all: <N> done, <M> parked, <K> failed; chain <prefix>` (or `BLOCKED: <reason>` if step 1 refused or the chain stalled).

---

## Guardrails

- **Never ask questions.** Autonomous batch mode — drive forward, report at end.
- **Drive in-loop, not via `/goal`.** A skill cannot fire the `/goal` built-in (user-invoked only). Iterate the chain inside this skill's own agentic loop using the Skill tool for `/mol:impl` and `/mol:commit`. Claude Code's automatic context summarization keeps a long chain going across turns; no `/goal` substrate is needed or available.
- **Don't duplicate `/mol:impl`.** All gates, TDD, simplify, acceptance, and status logic belongs to `/mol:impl`. This skill only iterates, verifies, and commits.
- **Trust the evaluator, not the self-report.** Per-spec advancement is gated on the independent Haiku-class evaluator subagent reading the actual spec + acceptance ledger — the same independence principle as `/goal`'s between-turn check.
- **Stop on stall or anomaly.** If the evaluator returns `stalled` or `anomaly`, stop the chain — later specs may depend on this one, and a discrepancy should be surfaced, not committed over.
- **Commit every spec.** Each spec gets its own checkpoint so the chain is reviewable mid-flight.
- **Read-only evaluator.** The evaluator subagent inspects and reports; it never edits specs, acceptance files, or code. Only `/mol:impl` (and `/mol:close`) may mutate status.

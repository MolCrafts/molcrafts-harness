---
name: impl-all
description: Default end-to-end implementer — discover a spec or chain under a prefix, drive /mol:impl per spec with independent completion checks, auto-run evaluators and /mol:close until every spec is done. Never asks questions; never leaves closing to the human. Prefer this over bare /mol:impl for any feature work.
argument-hint: "<spec-prefix or slug>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:impl-all — Batch Spec Chain Driver

Drive an entire spec chain (`<base>-01-<phase>`, `<base>-02-<phase>`, …) by iterating `/mol:impl` on each spec in order — each `/mol:impl` run commits and auto-closes its own spec. All gating, testing, simplifying, committing, and status advancement is `/mol:impl`'s job — this skill only discovers the chain, keeps it moving, and independently verifies each step before advancing.

```
/mol:impl-all morse-bond
→ finds morse-bond-01-potential, morse-bond-02-gradient, morse-bond-03-optimization
→ /mol:impl 01 → evaluator → /mol:impl 02 → evaluator → /mol:impl 03 → evaluator
→ reports chain verdict
```

**Never asks questions.** Fully autonomous — the skill drives the chain inside its own agentic loop (invoking `/mol:impl` via the Skill tool). Single-slug prefixes (one matching spec) are valid — still the preferred entry for "implement this feature end-to-end".

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

**2b. Evaluate (independent check — the `/goal` analogue).** After `/mol:impl` exits, do **not** trust its self-report. Dispatch a lightweight read-only evaluator subagent via the Agent tool with **`model: haiku`** (per `plugins/mol/rules/model-policy.md`). This mirrors what `/goal` does between turns — a fast, independent model confirms the completion condition — except scoped per spec instead of per turn. The evaluator is **read-only**; it never edits specs, acceptance files, or code.

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
  pending:        [ { id, type, owed_evaluator } ]   # owed_evaluator per
                  # plugins/mol/rules/evaluator-protocol.md § Type → owed evaluator
  reason:         <one line>
```

**2c. Act on the verdict:**

- `done` → next spec. (`/mol:impl` § 4c already committed and deleted the spec — no commit here.)
- `code-complete` → auto-invoke owed evaluators then `/mol:close <slug>` again (self-repair). Still code-complete after close → **stop the chain** with the close failure (do not ask the human to close). Close success → next spec.
- `stalled` → **stop the chain.** `/mol:impl` hit a blocker; later specs may depend on this one. Do not skip ahead.
- `anomaly` → **auto-invoke `/mol:close <slug>`** as self-repair. Close succeeds → treat as done, continue. Close refuses → **stop the chain** with the discrepancy (no human close recipe).

### 3. Report

Show one row per spec with its terminal status, using the evaluator's verdict (not the main-loop self-report).

```
═══ [mol:impl-all] chain verdict ═══

  morse-bond-01-potential      done
  morse-bond-02-gradient       done
  morse-bond-03-optimization   done

  3 done, 0 failed
```

If the chain stopped early, print the hard failure once (no human close menu). End-of-skill one-line summary: `/mol:impl-all: <N> done, <K> failed; chain <prefix>` (or `BLOCKED: <reason>`).

---

## Guardrails

- **Never ask questions.** Autonomous batch mode — drive forward, report at end.
- **Drive in-loop, not via `/goal`.** A skill cannot fire the `/goal` built-in (user-invoked only). Iterate the chain inside this skill's own agentic loop using the Skill tool for `/mol:impl` (and `/mol:close` on `anomaly`). Claude Code's automatic context summarization keeps a long chain going across turns; no `/goal` substrate is needed or available.
- **Don't duplicate `/mol:impl`.** All gates, TDD, simplify, acceptance, commit, and status logic belongs to `/mol:impl`. This skill only iterates and verifies.
- **Trust the evaluator, not the self-report.** Per-spec advancement is gated on the independent Haiku-class evaluator subagent reading the actual spec + acceptance ledger — the same independence principle as `/goal`'s between-turn check.
- **Stop on stall.** If the evaluator returns `stalled`, stop the chain — later specs may depend on this one. `anomaly` is first self-repaired via `/mol:close`; stop only if close refuses.
- **Auto-close every spec.** `/mol:close` runs after each spec (evaluators + agent-auto attestation). Never leave a close step for the human.
- **One checkpoint per spec — owned by `/mol:impl`.** Its § 4c/§ 4d finalize commits every spec, so the chain stays reviewable mid-flight; this skill never invokes `/mol:commit` or duplicates the close.
- **Read-only evaluator.** The evaluator subagent inspects and reports; it never edits specs, acceptance files, or code. Only `/mol:impl` (and `/mol:close`) may mutate status.

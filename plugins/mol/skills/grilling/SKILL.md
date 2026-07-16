---
name: grilling
description: Grill a plan or written spec relentlessly, one question at a time. Use when the user wants to stress-test a plan or design, uses any "grill" trigger, or when another skill needs a plan stress-test — `/mol:discuss` after converge (mode plan) and `/mol:spec` after persist (mode spec-audit). Read-only on source; returns a sharpened plan or audit result. Supports Chinese and English.
argument-hint: "[mode:plan|spec-audit] <plan, requirement, or slug>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:grilling — Plan / Spec Interrogation

Read CLAUDE.md → parse `mol_project:` (`$META`) so codebase exploration and recommended answers are project-aware (languages, layout, conventions, stage).

Model-invoked body of the grill procedure (callable by `/mol:discuss`, `/mol:spec`, free-form “grill me” phrasing, and the thin user entry `/mol:grill`). Relentless interview — one focused question at a time, each with a recommended answer — until the decision tree is resolved. Distinct from `/mol:discuss` (explores *whether / what*) and from `/mol:spec` (writes the binding artifact). Chain: discuss → **grilling (plan)** → user types spec → **grilling (spec-audit)** → impl.

## Mode selection

Parse `$ARGUMENTS` / caller preamble:

| Mode | When | Input |
|---|---|---|
| **plan** (default) | `/mol:grill`, `/mol:discuss` converge, free-form grill | one-paragraph plan / requirement (+ optional Context block) |
| **spec-audit** | `/mol:spec` after persist | `slug` + paths of written `<slug>.md` / `<slug>.acceptance.md` |

Explicit `mode: plan` or `mode: spec-audit` wins over inference. Infer `spec-audit` only when the caller is clearly `/mol:spec` post-persist or args name an existing spec slug under `$META.specs_path`.

## Procedure

### 1. Frame the surface under test

**plan mode.** Restate the plan / design in one sentence, in the user's language. List the code surface you read first — files, functions, related specs under `.claude/specs/`, notes under `.claude/notes/` — so questions and recommendations are grounded, not guessed.

No actual plan supplied (just an open-ended topic or "should we…?") → redirect to `/mol:discuss`; do not fabricate a plan to interrogate.

**spec-audit mode.** Restate: *"spec under audit: `<slug>`"*. Read the written Summary, Design (incl. Reuse decision), Files, Tasks, Out of scope, Testing, acceptance criteria, and librarian reuse resolution. List those sections + the code surface you cross-checked. Spec file missing → stop and tell the caller; do not invent a design.

### 2. Build the decision tree

Enumerate open decisions the surface implies and order them dependency-first — resolve upstream choices before the downstream ones they constrain. Hold this tree internally; do **not** dump it as a wall of questions. It is the queue for Step 3, and it grows or shrinks as answers land.

**plan mode** — decisions implied by the free-form plan.
**spec-audit mode** — gaps and under-specified choices **in the written artifact** (ambiguous tasks, unresolved reuse, missing acceptance coverage, contradictory out-of-scope, public-API shape left open). Do not re-litigate settled, clearly-written decisions unless they conflict with the codebase.

### 3. Interrogate — one question per turn

Each turn:

- Ask **exactly one** focused question about a single decision. Multiple questions at once is bewildering — never batch.
- Always include **your recommended answer** plus a one-line rationale grounded in `$META` / the code surface. Never ask a bare open question.
- If the answer is discoverable in the codebase, **explore and answer it yourself** instead of asking — state what you found and move on.
- Wait for the user's response before the next question. Fold the answer in; it may close downstream nodes or open new ones.

End every turn with a pulse:

```
Grill pulse
- Resolved: <decisions now settled, with the chosen answer>
- Open: <decisions still unresolved>
- Next: <the single question coming up>
```

Divergence guard: if the Open list keeps growing for two consecutive turns with no net reduction, the surface is under-formed for grilling — surface that and offer to drop back to `/mol:discuss` (plan mode) or leave the spec on disk for a re-spec (spec-audit mode). Relentless is the point; circling is not.

### 4. Converge

When the Open list is empty (every decision resolved or explicitly deferred as out-of-scope):

#### plan mode → hand off to `/mol:spec`

Assemble:

- a tightened one-paragraph (or short-bullet) **sharpened plan**, in the user's language, that a fresh `/mol:spec` could consume verbatim
- a **Decisions** log — each line `question → chosen answer → why`
- the relevant file paths from Step 1

Tell the user: *"sharpened. To produce the binding spec, run `/mol:spec <sharpened plan>`. Paste the Decisions log as additional context to capture the rationale."* Do **not** invoke `/mol:spec` or `/mol:impl`.

Return shape for callers:

```
audit_result: n/a (plan mode)
```

#### spec-audit mode → return audit result (caller writes)

Assemble:

- **Decisions** log — each line `question → chosen answer → why`
- `audit_result: clean` when no material design change is required (written artifact already matches resolved decisions)
- `audit_result: supersede_needed` when material holes were filled — include a short **supersede payload**: what must change in Design / Tasks / Files / acceptance (enough for `/mol:spec` to re-invoke `spec-writer` with `conflict_decision: supersede:<slug>`)

**This skill never writes specs or source.** `/mol:spec` owns supersede persistence when it is the caller. Standalone `/mol:grilling mode:spec-audit` reports the payload and tells the user to re-run `/mol:spec` (supersede) if needed.

On `clean`: tell the user the spec is grilled and ready for `/mol:impl <slug>`.

### 5. Redirect cleanly

When the *premise* dissolves under questioning — wrong feature, reopens into genuine *whether / what* exploration:

- **plan mode:** one sentence + reason → `/mol:discuss`. Write nothing.
- **spec-audit mode:** one sentence + reason → suggest `/mol:discuss`. Leave the written spec on disk (do not delete); user decides supersede or abandon.

## Output format

- Framing sentence + code-surface (and for spec-audit, sections read).
- Per-turn: one question + recommended answer + one-line rationale + `Grill pulse`.
- On converge (plan): sharpened plan + Decisions log + handoff to `/mol:spec`.
- On converge (spec-audit): Decisions log + `audit_result: clean | supersede_needed` (+ supersede payload when needed).
- On redirect: one-sentence reason + pointer; nothing else written by this skill.

One-line F2 summary:

```
/mol:grilling plan: sharpened (<N> decisions) → /mol:spec <one-line plan>
```

```
/mol:grilling spec-audit <slug>: clean (<N> decisions) → /mol:impl <slug>
```

```
/mol:grilling spec-audit <slug>: supersede_needed (<N> decisions) → caller supersedes
```

```
/mol:grilling: redirected → /mol:discuss (<reason>)
```

## Guardrails

- **Read-only on source and on specs.** Never edits files. Persistence of specs is `/mol:spec`; rules that fall out are `/mol:note`.
- **One question per turn.** Never batch questions.
- **Always recommend an answer.** Never ask a bare open question.
- **Self-answer from the codebase first.** Only ask the user what the code can't tell you.
- **No plan / no spec surface → no grill.** Redirect per Step 1.
- **Do not auto-invoke `/mol:spec` or `/mol:impl`.** Plan mode hands off; spec-audit returns a result to the caller.
- **Call `/mol:grilling`, never a user-only entry, from other skills.** Sibling auto-invoke targets this skill only.

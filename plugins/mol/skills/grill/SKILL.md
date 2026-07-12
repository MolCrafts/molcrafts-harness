---
description: Relentless one-question-at-a-time interview that hardens an already-formed plan or design before building — walks the decision tree dependency-first, recommends an answer for every question, and self-answers from the codebase where it can. Read-only; hands the sharpened plan to `/mol:spec`. Distinct from `/mol:discuss` (explores *whether / what* to do) — `/mol:grill` stress-tests a plan you *already have*. Supports Chinese and English.
argument-hint: "<the plan or design to stress-test>"
---

# /mol:grill — Plan Interrogation

Read CLAUDE.md → parse `mol_project:` (`$META`) so codebase exploration and recommended answers are project-aware (languages, layout, conventions, stage).

Relentless interview that takes a plan you *already have* and hammers it into shape — one focused question at a time, each with a recommended answer, resolving the decision tree dependency-first until the plan is sharp enough to spec. Distinct from `/mol:discuss` (explores *whether / what* — open-ended, can discard) and `/mol:spec` (writes the binding spec). `grill` is the bridge: discuss → **grill** → spec.

## Procedure

### 1. Frame the plan under test

Restate the plan / design being grilled in one sentence, in the user's language. List the code surface you read first — files, functions, related specs under `.claude/specs/`, notes under `.claude/notes/` — so questions and recommendations are grounded, not guessed.

No actual plan supplied (just an open-ended topic or "should we…?") → redirect to `/mol:discuss`; do not fabricate a plan to interrogate.

### 2. Build the decision tree

From the plan, enumerate the open decisions it implies and order them dependency-first — resolve upstream choices before the downstream ones they constrain. Hold this tree internally; do **not** dump it as a wall of questions. It is the queue you walk in Step 3, and it grows or shrinks as answers land.

### 3. Interrogate — one question per turn

The core loop. Each turn:

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

Divergence guard: if the Open list keeps growing for two consecutive turns with no net reduction, the plan is under-formed for grilling — surface that and offer to drop back to `/mol:discuss`. Relentless is the point, but circling is not.

### 4. Converge → hand off to `/mol:spec`

When the Open list is empty (every decision resolved or explicitly deferred as out-of-scope), assemble the **sharpened plan**:

- a tightened one-paragraph (or short-bullet) statement of the design with every resolved decision baked in, in the user's language, that a fresh `/mol:spec` could consume verbatim
- a **Decisions** log — each line `question → chosen answer → why` — capturing the rationale for the spec's *Why*
- the relevant file paths from Step 1

Tell the user: *"sharpened. To produce the binding spec, run `/mol:spec <sharpened plan>`. Paste the Decisions log as additional context to capture the rationale."* Do **not** invoke `/mol:spec` or `/mol:impl` yourself.

### 5. Redirect cleanly

When the plan dissolves under questioning — the premise turns out wrong, or it reopens into genuine *whether / what* exploration — say so in one sentence, name the reason, and redirect to `/mol:discuss`. Write nothing: no spec, no note, no `.claude/` artifact. A plan that isn't ready to harden belongs upstream, not in a half-formed spec.

## Output format

- Framing sentence + surfaced code-surface bullets (Step 1).
- Per-turn: one question + recommended answer + one-line rationale + `Grill pulse` block.
- On converge: sharpened plan + Decisions log + handoff instruction.
- On redirect: one-sentence reason + `/mol:discuss` pointer; nothing else.

One-line F2 summary:

```
/mol:grill <plan>: sharpened (<N> decisions resolved) → /mol:spec <one-line plan>
```

or

```
/mol:grill <plan>: redirected → /mol:discuss (<reason>)
```

## Guardrails

- **Read-only on code.** Never edits files; never writes specs or notes. Persistence is `/mol:spec` (plan) or `/mol:note` (a rule that fell out).
- **One question per turn.** Never batch questions.
- **Always recommend an answer.** Never ask a bare open question.
- **Self-answer from the codebase first.** Only ask the user what the code can't tell you.
- **No plan → no grill.** Redirect per Step 1.
- **Do not auto-invoke `/mol:spec` or `/mol:impl`.** Converge hands off; the user decides when to spec.

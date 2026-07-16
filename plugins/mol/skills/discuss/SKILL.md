---
name: discuss
description: Free-form design / improvement / scientific-insight discussion that drives toward convergence and either hands the agreed direction to `/mol:spec` or discards the thread. Use for exploratory threads (vs `/mol:spec` for already-clear requirements, `/mol:grill` for hardening an already-formed plan, or `/mol:note` for decided rules); read-only; supports Chinese and English.
argument-hint: "<topic or question>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:discuss — Design Discussion

Read CLAUDE.md → parse `mol_project:` (`$META`).

Conversational skill for working through design trade-offs, improvement ideas, or scientific insights *before* a spec. Two exit doors — **converge** (hand off to `/mol:spec`) or **discard** (leave no trace). Distinct from `/mol:spec` (requirement already clear), `/mol:grill` (hardens a plan you *already have* — grill needs a concrete plan, discuss explores *whether / what*), and `/mol:note` (captures *decided* rules).

## Procedure

### 1. Frame the topic

Restate the topic in one sentence in the user's language. List relevant code surface — files, functions, prior commits, related specs under `.claude/specs/`, related notes under `.claude/notes/` — that you read before responding.

Genuinely vague → ask one targeted clarifying question and stop. Don't explore on a wrong premise.

### 2. Drive toward convergence

Each turn, end with a pulse:

```
Convergence pulse
- Agreed: <bullets of what is now settled>
- Open: <bullets of what is still in dispute or undefined>
- My read: converging | diverging | stuck
```

Convergence signals (any one): user says "yes / 同意 / let's do it"; open list empty; two consecutive turns produce no new "Open" items.

Divergence signals: open list grows turn-over-turn; user keeps reframing topic; both keep proposing mutually incompatible alternatives without reduction.

Hard cap: **8 turns**. At turn 8 → force verdict (Step 3 or 4).

### 3. Converge → hand off to `/mol:spec`

When pulse reads "converging" *and* open list is empty (or user accepts remaining opens as out-of-scope):

- one-paragraph requirement, in user's language, that a fresh `/mol:spec` could consume verbatim
- short "Context from discussion" block listing alternatives considered and reason this won — becomes spec's *Why*
- relevant file paths from Step 1

Tell the user: *"converged. To produce the binding spec, run `/mol:spec <one-paragraph requirement>`. Paste the Context block as additional context if you want the trade-off rationale captured."* Do not invoke `/mol:spec` yourself.

### 4. Discard cleanly

When pulse reads "diverging" or "stuck" for two consecutive turns, when user changes mind, when question dissolves into a non-question, or when 8-turn cap fires without convergence:

- say so explicitly + name the reason in one sentence (e.g. *"discarded — depends on a decision in `auth/` that hasn't been made yet"*)
- write nothing: no notes, no draft spec, no `.claude/notes/` entry, no `.claude/specs/` entry
- if a *stable rule* fell out (rare), suggest user run `/mol:note` separately — do not promote yourself

Discard is first-class. Not-converging is fine; shipping a half-decided spec is not.

## Output format

- Framing sentence + surfaced code-surface bullets (Step 1).
- Per-turn `Convergence pulse` block.
- On convergence: one-paragraph requirement + Context block + handoff instruction.
- On discard: one-sentence reason; nothing else.

One-line F2 summary:

```
/mol:discuss <topic>: converged → /mol:spec <one-line requirement>
```

or

```
/mol:discuss <topic>: discarded (<reason>)
```

## Guardrails

- **Read-only on code.** Never edits files. Spec written by `/mol:spec`.
- **Do not promote** outputs into `.claude/specs/` or `.claude/notes/notes.md`. Convergence hands off; discard leaves no trace.
- **Do not silently merge with `/mol:note`.** Stable rule emerges → surface as `/mol:note` suggestion.
- **Do not auto-loop or auto-invoke `/mol:spec`.** User decides.
- **Hard 8-turn cap.**

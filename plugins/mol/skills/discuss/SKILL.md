---
name: discuss
description: "Structured design discussion with Convergence pulse; converge → auto /mol:grilling, or discard. Free-form: 该不该做/几种方案/should we/trade-offs — load this skill, not bare chat. Not for clear specs (/mol:spec), formed plans (/mol:grilling), or decided rules (/mol:note). Read-only."
argument-hint: "<topic or question>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:discuss — Design Discussion

Read CLAUDE.md → parse `mol_project:` (`$META`).

Conversational skill for working through design trade-offs, improvement ideas, or scientific insights *before* a spec. Two exit doors — **converge** (package requirement → auto-invoke `/mol:grilling` plan mode) or **discard** (leave no trace). Distinct from `/mol:spec` (requirement already clear), `/mol:grilling` (hardens a plan you *already have*), and `/mol:note` (captures *decided* rules).

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

### 3. Converge → auto-invoke `/mol:grilling` (plan mode)

When pulse reads "converging" *and* open list is empty (or user accepts remaining opens as out-of-scope):

1. Produce:
   - one-paragraph requirement, in user's language, that a fresh `/mol:spec` could consume verbatim
   - short "Context from discussion" block listing alternatives considered and reason this won — becomes the grill Decisions seed / later spec *Why*
   - relevant file paths from Step 1
2. Tell the user briefly: *"converged — entering `/mol:grilling` to stress-test the plan before you spec."*
3. **Auto-invoke `/mol:grilling`** in **plan** mode with the one-paragraph requirement + Context block as the plan under test. Use the Skill tool (Claude) or read-and-execute `../grilling/SKILL.md` (Codex). Never call user-only `/mol:grill`.
4. After grilling finishes, its own handoff applies: sharpened plan → tell the user they can ignite spec with a short phrase (落盘 / 写 spec / "spec this") — slash optional. **Do not** invoke `/mol:spec` from discuss (tier C gate).

### 4. Discard cleanly

When pulse reads "diverging" or "stuck" for two consecutive turns, when user changes mind, when question dissolves into a non-question, or when 8-turn cap fires without convergence:

- say so explicitly + name the reason in one sentence (e.g. *"discarded — depends on a decision in `auth/` that hasn't been made yet"*)
- write nothing: no notes, no draft spec, no `.claude/notes/` entry, no `.claude/specs/` entry
- do **not** invoke grilling
- if a *stable rule* fell out (rare), suggest `/mol:note` (harness sync — will supersede fossils, not append) — do not write notes yourself

Discard is first-class. Not-converging is fine; shipping a half-decided spec is not.

## Output format

- Framing sentence + surfaced code-surface bullets (Step 1).
- Per-turn `Convergence pulse` block.
- On convergence: one-paragraph requirement + Context block + auto-invoke `/mol:grilling` (then grilling's output).
- On discard: one-sentence reason; nothing else.

One-line F2 summary:

```
/mol:discuss <topic>: converged → /mol:grilling → (user) /mol:spec <one-line requirement>
```

or

```
/mol:discuss <topic>: discarded (<reason>)
```

## Guardrails

- **Read-only on code.** Never edits files. Spec written by `/mol:spec`.
- **Do not promote** outputs into `.claude/specs/` or `.claude/notes/notes.md`. Convergence hands off to grilling; discard leaves no trace.
- **Do not silently merge with `/mol:note`.** Stable rule emerges → surface as `/mol:note` suggestion.
- **Auto-invoke `/mol:grilling` on converge; never auto-invoke `/mol:spec`.** User decides when to spec after grilling.
- **Hard 8-turn cap.**

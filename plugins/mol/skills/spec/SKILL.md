---
description: Convert a natural-language requirement into a structured technical spec under .claude/specs/, with a checkbox-tracked Tasks section, then negotiate the binding `<slug>.acceptance.md` contract that defines "done". The bulk drafting + self-validation is delegated to the `spec-writer` agent (subagent context, not parent); this skill orchestrates conflict detection, user approval, and persistence. Detects conflicts with existing specs and updates the old spec body + regenerates acceptance criteria when superseded or refined. Writes specs and acceptance files (and amends old ones during conflict resolution). Supports Chinese and English.
argument-hint: "<feature description>"
---

# /mol:spec — Specification Generator

Read CLAUDE.md. Parse `mol_project:` (`$META`). If missing, emit the
adoption hint and stop.

Resolve the specs path:

1. If `$META.specs_path` is set, use it (canonical default
   `.claude/specs/`).
2. Otherwise, default to `.claude/specs/`.

Create the directory if missing.

## Specs are active runtime artifacts

Specs live under `.claude/` because they are **alive**: `/mol:impl`
ticks their checkboxes off as work progresses, and the spec file is
**deleted** when every task is complete. A spec is not documentation
— it is a working contract between this conversation and the next
one.

This skill produces **two** files per spec:

- `<slug>.md` — the design (Summary / Design / Files / Tasks /
  Testing / Out of scope).
- `<slug>.acceptance.md` — the binding "done" contract: structured
  observable criteria that `/mol:impl` and any runtime evaluator
  (e.g. `/mol:web` for UI) verify against. Format defined in
  `plugins/mol/docs/evaluator-protocol.md`.

The pair is produced together. `/mol:impl` refuses to start without
both files in place — this is the planner→generator handoff
formalized.

Where specs do **not** belong:

- `docs/` — public documentation. Never put a spec there.
- `.agent/` — passive context (notes, decisions, debt). Specs are
  not passive; they are active runtime tasks.

## Procedure

### 1. Parse the request

What capability is being added? Which layer / package / crate is
affected? Derive the kebab-case slug. State this in one sentence
before going further.

### 2. Search domain basis (if applicable)

If physics is involved AND `$META.science.required` is `true`,
delegate to the `scientist` agent for equations, references, and
validation targets. Capture the scientist's output verbatim — it
becomes input to `spec-writer` in Step 5.

### 3. Conflict check (MANDATORY before any write)

Read every existing spec under `$META.specs_path`. For the new
request, classify against each existing spec:

- **Duplicate.** The existing spec already covers this scope →
  tell the user, don't add a sibling.

- **Supersede / refine.** The new request changes, expands, or
  fixes the design of an existing spec → **update the old spec
  in place**, do not create a sibling. Read the old spec body
  in full; you will pass it to `spec-writer` so it can reconcile
  the Tasks list.

- **Independent.** Different scope from any existing spec → safe
  to create a new file.

State the classification before continuing. Never create a
sibling spec for a supersede / refine. If you find yourself
wanting to create `morse-bond-v2.md` next to `morse-bond.md`,
that's the wrong move — feed both into `spec-writer` with
`conflict_decision: supersede:morse-bond`.

### 4. Scan interaction points

Glob the project root for files relevant to `$META.language`.
Identify the closest existing pattern. Flag any new public API,
data-model change, or cross-layer dependency. Capture as
structured input for `spec-writer`.

### 4.5. Consult `librarian` (planning-time placement & reuse)

Before handing the request to `spec-writer`, ask the `librarian`
agent to look at what's already in the codebase (via the project
blueprint at `.agent/architecture.md`) and answer two questions:
*"is this already there?"* and *"where does it canonically belong?"*

Invoke `librarian` with a structured prompt:

- `request` — the user's requirement (preserve language).
- `scope_layer` — from Step 1.

`librarian` returns one of two shapes:

- **Shape A — fresh blueprint, full report** with four fixed
  sections: `Reuse candidates`, `Recommended placement`,
  `Closest pattern`, `Confidence`.
- **Shape B — `stale: true`** with a one-line reason.

#### Stale-handling branch (skill orchestrates; O2 preserved)

If `librarian` returned `stale: true`, **the skill** — not the
agent — owns the recovery routing. `librarian` MUST NOT invoke
`architect`, and `architect` MUST NOT invoke `librarian`. The
chain is:

1. this skill invokes `architect` in `mode: inventory` (the
   architect inventory mode) to draft a fresh catalog;
2. this skill invokes `/mol:map` (which gates on the user-confirm
   step) to write the refreshed `.agent/architecture.md`;
3. this skill re-consults `librarian` (the librarian re-consult)
   and now expects Shape A.

If at any point the user defers the `/mol:map` write gate, fall
back to drafting `spec-writer` input without a librarian report
(noting "librarian consult skipped — blueprint refresh deferred"
in the Step 6 surfacing).

Capture the final librarian report verbatim — it becomes a new
input field `librarian_report` to `spec-writer` in Step 5.

### 5. Delegate drafting to `spec-writer`

Invoke the `spec-writer` agent with a structured prompt
containing:

- `request` — the user's requirement (preserve language).
- `scope_layer` — from Step 1.
- `scientist_output` — from Step 2 (or empty).
- `conflict_decision` — `independent` or `supersede:<slug>`
  (with the old spec body inlined when supersede).
- `interaction_points` — from Step 4.
- `slug` — from Step 1.

The agent drafts the spec body (Summary / Domain basis / Design
/ Files / Tasks / Testing strategy / Out of scope), self-validates
against the quality checklist (sections / atomic tasks /
RED-before-GREEN / Files↔Tasks cross-reference), and proposes
acceptance criteria. It returns two markdown blocks plus a
status line; **it does not write to disk**.

Branch on the agent's `Status:`:

- `Status: ok` — proceed to Step 6.
- `Status: blocked` — surface the failed items to the user with
  the question: *"I cannot satisfy <items>; do you want to
  relax X, or refine the request?"* Stop until the user
  responds; on response, re-invoke `spec-writer` from Step 5.
- `Status: split-needed` — show the proposed cut to the user
  and ask if they want to spec the parts separately. If yes,
  re-invoke once per part.

For supersede flows the agent additionally returns a `Diff vs.
previous spec` block; you will surface that diff in Step 6 so
the user sees what was unchecked, removed, and added before
approving.

### 6. Show, confirm, persist

Show the user **both** files (spec body + acceptance) in the
same turn, exactly as `spec-writer` returned them. Call out:

- **librarian's reuse candidates and recommended placement** from
  Step 4.5 (surface this *first*, before any other callout — the
  user must see and acknowledge what was already in the codebase
  before approving a draft that may have ignored it),
- the criteria derived from Testing strategy (easy to miss),
- spec items deliberately not turned into criteria, with a
  one-line reason,
- (supersede) the diff against the previous spec.

Wait for explicit approval. Edits — adding/removing/retyping
criteria, tightening `pass_when`, moving items to
`out_of_scope` — are acceptable. If the user requests changes,
either:

- apply them inline if they're surface tweaks (rename a
  criterion id, sharpen a pass_when), or
- if they materially change the design (new task, removed
  file, retyped criterion), re-invoke `spec-writer` with the
  amended request.

After approval:

1. Write `{$META.specs_path}{slug}.md` with the spec body the
   agent returned. For supersede, this overwrites the old
   file; bump `revised: YYYY-MM-DD` in the frontmatter (do
   not change `created`).

2. Write `{$META.specs_path}{slug}.acceptance.md` per the
   schema in `plugins/mol/docs/evaluator-protocol.md`.

3. Update `{$META.specs_path}INDEX.md`:

   ```markdown
   # Specs

   - [{slug}]({slug}.md) — <one-line summary> [approved]
   ```

   On supersede/refine, update the entry in place. When
   `/mol:impl` finishes a spec, it removes the entry.

If the user defers approval (*"let me think about it"*),
write the spec with `status: draft` and skip writing
`acceptance.md`. Re-invoking `/mol:spec` on the same slug
resumes from Step 5 (which will re-invoke `spec-writer`).

### 7. Report

Print:

- spec path + acceptance path
- task count (e.g. *"7 tasks; 0 completed"*)
- criteria count, broken down by `type`
- one-line note flagging which criteria need a runtime
  evaluator (any `type` other than `code` / `docs`). Example:
  *"3 ui_runtime criteria — invoke `/mol:web <slug>` after
  `/mol:impl` finishes."*
- for supersede flows: a short diff (what changed, what was
  unchecked, what was removed, what was added)

End with a one-line user-facing summary.

## Lifecycle

- `draft` — written but the user deferred approval; acceptance.md
  not yet written. Re-run `/mol:spec <slug>` to resume.
- `approved` — user signed off both spec body and `<slug>.acceptance.md`.
  This is the ready-to-impl state.
- `in-progress` — `/mol:impl` started; tasks being ticked off.
- `done` — every task is `[x]`; tests green. `/mol:impl` deletes
  the spec file, the INDEX entry, and `<slug>.acceptance.md` on
  its way out.

## Why drafting is delegated

The bulk of `/mol:spec`'s work — drafting prose, listing files,
breaking the work into atomic tasks, walking the self-validation
checklist, proposing acceptance criteria — is one long generative
pass. Doing that in the parent context burns tokens that the
ensuing `/mol:impl` run (and the rest of the conversation) needs.
The `spec-writer` subagent runs in its own context window and
returns only the finished markdown. The parent retains the
result, not the drafting trail.

The user-interaction parts (conflict triage, approval gate,
persistence, INDEX update) stay in the parent because they
require dialogue with the user and atomic file-system writes —
neither fits a one-shot subagent.

See `plugins/mol/docs/agent-design.md` for the full producer /
reviewer / drafter classification.

## Bilingual

If the user argument is in Chinese, `spec-writer` produces the
spec body in Chinese; the frontmatter keys, INDEX entry, and
the verb-prefix of each Tasks line stay in English so
`/mol:impl` and downstream tooling parse the checklist
deterministically.

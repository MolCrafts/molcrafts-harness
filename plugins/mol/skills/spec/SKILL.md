---
description: Convert a natural-language requirement into a structured spec under `.claude/specs/` plus a binding `<slug>.acceptance.md` contract that defines "done". Persists both files directly — no approval prompt. Use to start any non-trivial feature; detects conflicts with existing specs and supports Chinese and English.
argument-hint: "<feature description>"
---

# /mol:spec — Specification Generator

Read CLAUDE.md → parse `mol_project:` (`$META`); else emit adoption hint and stop. Resolve `$META.specs_path` (default `.claude/specs/`); create dir if missing.

Produces `<slug>.md` (design) + `<slug>.acceptance.md` (binding "done" contract per `plugins/mol/rules/evaluator-protocol.md`). `/mol:impl` refuses without both; deletes both when done. Specs live under `.claude/specs/` — never `docs/` or `.claude/notes/`.

## Procedure

### 1. Parse & research

Derive kebab-case slug. State in one sentence.

**Conflict check** — read every existing spec under `$META.specs_path`:
- **Duplicate** → tell user, stop.
- **Supersede/refine** → update old spec in place. Pass old body to `spec-writer` as `conflict_decision: supersede:<slug>`.
- **Independent** → safe to create.

**Domain & placement** — run in parallel where possible:
- Physics + `$META.science.required: true` → delegate to `scientist` for equations/references. Capture verbatim.
- Glob for relevant files; flag new public API, cross-layer deps.
- Consult `librarian` (reads `.claude/notes/architecture.md`) for reuse candidates + recommended placement. If `librarian` returns `stale: true`: invoke `architect` (inventory mode) → `/mol:map` (user-confirmed) → re-consult `librarian`. If user defers `/mol:map`, note "blueprint refresh deferred" and proceed.

### 2. Delegate drafting to `spec-writer`

Invoke `spec-writer` with: `request`, `slug`, `scope_layer`, `scientist_output`, `conflict_decision`, `interaction_points`, `librarian_report`.

`spec-writer` drafts spec body (Summary / Domain basis / Design / Files / Tasks / Testing / Out of scope) + acceptance criteria, self-validates, returns markdown **without writing to disk**.

Branch on `Status:`:
- `ok` → proceed to Step 3.
- `blocked` → surface failed items. User relaxes or refines; re-invoke from Step 2.
- `split-needed` → large-spec split rule fired (`plugins/mol/rules/large-spec-split.md`). **Don't prompt.** Re-invoke `spec-writer` once per sub-slug in chain order with `slug: <base>-NN-<phase>`, `request: sub-scope`, `conflict_decision: independent`. Collect full chain; proceed to Step 3.

### 3. Persist & show

Persist immediately — **no approval prompt, no waiting**:
1. Write `{$META.specs_path}{slug}.md` with `status: approved` (overwrite for supersede; bump `revised`). Chain → one per sub-spec; no parent file.
2. Write `{$META.specs_path}{slug}.acceptance.md`. Chain → one per sub-spec.
3. Update `{$META.specs_path}INDEX.md`:
   ```
   - [{slug}]({slug}.md) — <one-line summary> [approved]
   ```
   Chain → one entry per sub-spec. Supersede → update in place.

Then show spec body + acceptance exactly as written. Call out: librarian reuse candidates (first), criteria from Testing strategy, UI checks recorded in the spec body's **UI verification** section (never acceptance criteria), items deliberately not turned into criteria, supersede diff if any.

Post-persist tweaks from the user → apply in place. Material design changes → re-invoke `spec-writer` (supersede) and overwrite.

### 4. Report

Spec path(s), task count, criteria count by `type`, runtime-evaluator flag (any non-`code`/`runtime` type → print evaluator hint). Chain → next-step pointer: *"start with `/mol:impl <base>-01-<phase>`"*. End with one-line summary.

## Guardrails

- **Chinese input** → `spec-writer` produces body in Chinese; frontmatter keys, INDEX entry, and Tasks verb-prefixes stay English for downstream tooling.
- **Drafting is delegated** to `spec-writer` to keep parent context free for conversation. Triage, persistence, and INDEX upkeep stay here; persistence is automatic — never wait for approval. See `plugins/mol/rules/agent-design.md`.
- **UI-runtime checks never become acceptance criteria.** They live in the spec body's **UI verification** section (non-binding); `/mol:web` verifies them ad hoc and they never park a spec at `code-complete`.
- **Spec lifecycle** (`draft` → `approved` → `in-progress` → `code-complete` → `done`) is defined in `plugins/mol/rules/evaluator-protocol.md`.

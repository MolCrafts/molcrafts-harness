---
description: Implementation workflow — scope → spec → acceptance gate → TDD → implement → verify. Use after `/mol:spec` has produced an approved spec + acceptance file; writes code, tests, and docs while ticking the spec's Tasks/acceptance checkboxes.
argument-hint: "<feature description or path to spec file>"
---

# /mol:impl — Spec Tasks Orchestrator

Read CLAUDE.md → parse `mol_project:` (`$META`); else emit adoption hint and stop. Print `[mol] stage: <value>`.

`/mol:impl` orchestrates a spec's Tasks checklist: pre-flight → iterate each task (RED → GREEN → tick) → verify → simplify → finalize (acceptance ledger + commit + status decision). All stage-policy decisions delegate to `/mol:simplify` (the single backward-compat gatekeeper, `plugins/mol/rules/stage-policy.md`).

---

## 1. Pre-flight

### 1a. Scope & branch

Classify against `$META.arch.style`: SMALL (<3 files, existing pattern) / MEDIUM (3–8 files, new pattern) / LARGE (new top-level concept).

LARGE on a monolithic spec → stop, re-invoke `/mol:spec` to produce a chain.

When slug matches `<base>-<NN>-<phase>` or scope is LARGE: if on default branch, checkout `feat/<base>` (create if needed). No prompt. Silent otherwise.

State classification. SMALL skips to § 2.

### 1b. Spec gates

Read `{$META.specs_path}{slug}.md` + `{$META.specs_path}{slug}.acceptance.md`. Refuse if either missing.

**Status gate:**
- `draft` → refuse (re-run `/mol:spec`).
- `approved` → first run.
- `in-progress` → resume (run 1c).
- `code-complete` → skip to § 4.
- `done` → warn (should be deleted).

**Stage gate:** `maintenance` refuses unless spec has `kind: bugfix`.

**Acceptance gate:** parse `criteria:` from acceptance frontmatter. Each `type: code | runtime` criterion must map to ≥1 task. Surface the ledger. Already-`verified` criteria are not re-traced unless 1c finds the test path gone.

### 1c. Resume sync

For every unchecked task, cheap inspection (grep symbol, glob file, run `$META.build.test_single`). Show verdict per task:

```
[done — verified]      Implement Foo in src/foo.py        → tick
[no evidence]          Wire Bar into Service              → leave
```

Replace `- [ ]` with `- [x]` for verified tasks in one batch. Report: *"N of M tasks already done; resuming from X."* If all done → skip to § 3.

Set `status: in-progress`.

### 1d. Architecture check (MEDIUM/LARGE)

Verify placement against `$META.arch.rules_section`. LARGE → delegate to `architect`.

---

## 2. Core loop — iterate Tasks

For each unchecked task, in order:

### 2a. TDD (RED)

First **Write failing tests** task → delegate to `tester` agent. Required categories: happy path, edge cases, immutability, domain validation (if `$META.science.required`). Run `$META.build.test_single`; confirm red. **Tick immediately.**

### 2b. Implement (GREEN)

For each remaining task:
1. Make the change.
2. Run `$META.build.test`; confirm green.
3. Stay inside the layer from 1d.
4. **Tick that task's box.**

Task infeasible → stop, re-invoke `/mol:spec` (supersede).

Every line — production or test — satisfies `$META.build.check`. No escape-hatch types (`Any`, `any`, `interface{}`).

MEDIUM/LARGE: after impl tasks, re-delegate to `architect` for post-impl layer check.

---

## 3. Verify & simplify

Run in parallel: `$META.build.check` + `$META.build.test` (full suite). MEDIUM/LARGE: delegate to `documenter` for docstrings per `$META.doc.style`.

Invoke `/mol:simplify` on touched files. **Mandatory.** `/mol:simplify` decides: delete legacy (`experimental`) / shim (`stable`) / migration-note (`beta`) / leave (`maintenance`). Runs its own build/test gate; reverts on regression.

If revert → leave `in-progress`, surface trigger, stop. User resolves; re-run `/mol:impl`; 1c recovers.

If "Hygiene cleanup" task exists → tick it; else add one line recording simplify ran clean.

---

## 4. Finalize

Re-read spec + acceptance.

### 4a. Update acceptance ledger

For each `type: code | runtime` criterion, write back verdict (`verified` / `failed`) with `last_checked` date. Leave criteria of other types untouched.

### 4b. Decide status

All Tasks `[x]`, build green, every `code` / `runtime` criterion `verified` — any failing → leave `in-progress`, print remaining tasks + unmet criteria, stop.

All hold:
- Acceptance has only `code` / `runtime` criteria → **done** (§ 4c).
- Any other-typed criterion exists → **code-complete** (§ 4d).

### 4c. Done path

1. Mark `status: done`.
2. Invoke `/mol:commit` (gates on `/mol:ship commit`). Message: `feat(<scope>): <summary> (<slug>)`. BLOCK → leave `in-progress`, stop.
3. Delete spec, acceptance, INDEX entry.
4. Suggest `/mol:note` for non-obvious context.

### 4d. Code-complete path

1. Mark `status: code-complete`.
2. Invoke `/mol:commit` (same as done path). BLOCK → drop to `in-progress`, stop.
3. List the criteria left at `pending`, **grouped by evaluator owed** (per `evaluator-protocol.md`):
   - `type: performance | scientific` → owed to `/mol:bench` (or `/mol:close --manual` if `mol_project.bench.repo` is not configured)
   - `type: ui_runtime` → owed to `/mol:web`
   - `type: docs` → owed to a human reviewer (or `/mol:close --manual`)
   - any criterion with `evaluator_hint:` set → owed to that specific evaluator
4. Print the **closing recipe** verbatim, so the operator knows exactly how to advance the spec from `code-complete` → `done`:

   ```
   PARKED at code-complete. To advance to `done` and delete the spec:

     1. Run the owed evaluator(s) listed above; each flips its criteria
        to status: verified.
     2. Re-run `/mol:impl <slug>` — when every criterion is verified,
        §4 advances to done and deletes the spec, acceptance, and INDEX entry.

   Manual close (no evaluator available, operator has observed conditions
   met externally):

     /mol:close <slug> --manual

     — flips every pending criterion to verified with a manual-promote
     audit note, then advances to done. Use only when you have actually
     observed the pass_when condition; the audit trail lands in the
     commit message.
   ```

5. Do not delete spec/acceptance/INDEX.

For chained specs, exit cleanly after commit — don't auto-advance.

---

## 5. Summary

One line: scope, files changed, tests passing, resulting `status:` (`done` / `code-complete` with N pending / `in-progress` with N remaining), acceptance tally.

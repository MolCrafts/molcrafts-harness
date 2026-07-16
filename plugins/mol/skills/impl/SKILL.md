---
name: impl
description: Implementation workflow — scope → spec → acceptance gate → TDD → implement → verify → auto simplify + close. Use after `/mol:spec` has produced an approved spec + acceptance file; writes code, tests, and docs while ticking the spec's Tasks/acceptance checkboxes, then auto-invokes `/mol:simplify` and `/mol:close` without prompting.
argument-hint: "<feature description or path to spec file>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:impl — Spec Tasks Orchestrator

Read CLAUDE.md → parse `mol_project:` (`$META`); else emit adoption hint and stop. Print `[mol] stage: <value>`.

`/mol:impl` orchestrates a spec's Tasks checklist: pre-flight → iterate each task (RED → GREEN → tick) → verify → simplify → finalize (acceptance ledger + commit + auto-close). `/mol:simplify` and `/mol:close` run automatically every pass — never prompt the operator for either. All stage-policy decisions delegate to `/mol:simplify` (the single backward-compat gatekeeper, `plugins/mol/rules/stage-policy.md`).

Orchestration mode per `plugins/mol/rules/model-policy.md`: this loop plans, routes, gates, and verifies — it never authors production source. Tests come from `tester`, production code from `implementer`.

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

Task targets `regressions/` (the spec's end-to-end regression example) → it is a test artifact: delegate to `tester` (write-mode, § Regression examples in its prompt), run the example standalone, tick on pass. `implementer` never writes it.

For each remaining task:
1. Delegate to `implementer` agent with: spec path, the task line, the RED test reference from 2a (command in `$META.build.test_single` form), the spec's Files section as scope, and the layer from 1d.
2. `verdict: green` → run `$META.build.test_single` yourself to confirm (never trust the self-report), then **tick that task's box** — ticking stays here; `implementer` never ticks.
3. `still-red` → re-delegate once with the failure output attached; still red after the retry → stop, re-invoke `/mol:spec` (supersede).
4. `blocked:` → surface the blocker verbatim and stop (missing RED test → run 2a for that symbol; spec ambiguity → `/mol:spec`).

Revert on regression is this skill's job (and `/mol:simplify`'s inside § 3); `implementer` never reverts.

Every line — production or test — satisfies `$META.build.check`. No escape-hatch types (`Any`, `any`, `interface{}`).

MEDIUM/LARGE: after impl tasks, re-delegate to `architect` for post-impl layer check.

---

## 3. Verify & simplify

Run in parallel: `$META.build.check` + `$META.build.test` (full suite) + the spec's `regressions/` example(s) standalone. A failing regression example blocks finalize exactly like a failing test — the feature is not delivered until the end-to-end example reproduces its reference values. MEDIUM/LARGE: delegate to `documenter` for docstrings per `$META.doc.style`.

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
3. List the criteria left at `pending`, **grouped by evaluator owed** per the routing table in `plugins/mol/rules/evaluator-protocol.md` § *Type → owed evaluator*.
4. **Auto-close.** Invoke `/mol:close <slug>` (default mode) — no prompt. It re-checks the ledger and either advances to `done` + deletes spec/acceptance/INDEX, or leaves the spec parked and names what each pending criterion still owes.
5. If still parked after auto-close, end with one line — `parked at code-complete; owes <evaluator(s)> for <criterion ids>` — and stop. No recipe block, no questions.
6. Never delete spec/acceptance/INDEX directly on this path — deletion is `/mol:close`'s job.

For chained specs, exit cleanly after commit + auto-close — don't start the next spec (that's `/mol:impl-all`'s job).

---

## 5. Summary

One-line F2 summary: scope, files changed, tests passing, resulting `status:` (`done` / `code-complete` with N pending / `in-progress` with N remaining), acceptance tally.

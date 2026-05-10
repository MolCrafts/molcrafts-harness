---
description: Implementation workflow — scope, optional litrev, spec, **acceptance gate** (refuse to start unless `<slug>.md` is `status: approved` AND `<slug>.acceptance.md` exists), **resume sync** (detect tasks already done out-of-band and reconcile checkboxes before doing new work), architecture check, TDD, implement, verify. Reads the spec's Tasks checklist and the acceptance contract; ticks each box as work completes; on full completion, marks status done and deletes the spec file, the acceptance file, and the INDEX entry. Writes code, tests, docs; edits the spec file (checkboxes + status). Reads mol_project frontmatter from CLAUDE.md.
argument-hint: "<feature description or path to spec file>"
---

# /mol:impl — Implementation

Read CLAUDE.md. If the first block is a `mol_project:` frontmatter,
parse it; otherwise print the adoption hint and stop. Let `$META`
refer to the parsed frontmatter throughout.

## Step 1 — Assess scope

Classify the task against `$META.arch.style`:

- **SMALL** — single new symbol following an existing pattern, < 3
  files. Skip to Step 3.
- **MEDIUM** — 3–8 files, introduces a new pattern, fits existing
  layers. Start at Step 2.
- **LARGE** — new top-level concept (new driver / new package / new
  layer / new frame field). LARGE scope is also a trigger for the
  large-spec split rule (`plugins/mol/rules/large-spec-split.md`);
  if the spec on hand is monolithic LARGE, stop and re-invoke
  `/mol:spec` so the rule fires and produces a chain. Otherwise,
  continue full pipeline from Step 2 on the current sub-spec.

State the scope classification and confirm with the user before
proceeding.

## Step 1.5 — Auto-branch (chained / LARGE features)

Per `plugins/mol/rules/large-spec-split.md`, when the slug being
implemented matches the chain pattern `<base>-<NN>-<phase>` **or**
the scope is LARGE, ensure work happens on a feature branch
without prompting.

1. Resolve the project default branch as `upstream`'s default if
   `upstream` exists, else `main` if it exists, else `master`.
2. If the current branch equals the default branch, create and
   check out `feat/<base>` (or check it out if it already exists
   and is reachable from the default). Do not prompt; print one
   line: `/mol:impl: switched to branch feat/<base>`.
3. If the current branch is anything other than the default, stay
   on it — the user has positioned themselves deliberately.

This step is silent for SMALL and MEDIUM scope on a single,
non-chained spec.

## Step 2 — Domain & spec (MEDIUM / LARGE only)

- If the feature involves equations or physics AND
  `$META.science.required` is `true`: invoke `/mol:litrev`. Abort if
  no credible basis.
- If `$ARGUMENTS` is a path under `$META.specs_path`, read that file
  as the spec.
- Otherwise, invoke `/mol:spec` to produce a spec with a Tasks
  checklist, then read the resulting file.

Once the spec is in hand:

### 2a. Status gate (HARD — never bypass)

Read the spec frontmatter's `status:` field and branch:

- `status: draft` — refuse. The user deferred approval mid-`/mol:spec`;
  tell them to re-run `/mol:spec <slug>` to resume from the
  approval step (which writes acceptance.md on confirm).
- `status: approved` — first run; continue to 2a-bis.
- `status: in-progress` — a previous run was interrupted, **or work
  was done out-of-band**. Continue to 2a-bis; sync (2c) will reconcile.
- `status: done` — Step 7 should have already deleted this spec.
  Warn the user and stop; let them either delete the spec by hand
  or open a new one with `/mol:spec`.

### 2a-bis. Acceptance contract gate (HARD)

Read `{$META.specs_path}{slug}.acceptance.md`. If absent, refuse —
tell the user the spec was approved without an acceptance file
(this should be impossible from `/mol:spec`, so it means manual
tampering or a partial supersede). Either restore the file from
git or re-run `/mol:spec <slug>` to regenerate it.

Parse the `criteria:` list from the frontmatter. This is the
binding "done" contract for the rest of this run:

- Every Step 4 RED test MUST trace back to at least one criterion
  whose `type` is `code` or `runtime` (and is verifiable by the
  test suite). State the trace for each test you write.
- Criteria with `type` ∈ {`ui_runtime`, `scientific`,
  `performance`, `docs`} are **out of scope for `/mol:impl`'s
  built-in verification**. Do not skip them — surface them at
  Step 7 close-out so the user knows which runtime evaluator to
  invoke next (`/mol:web` for `ui_runtime`, etc.).
- If a criterion has no plausible mapping to any planned task,
  stop and tell the user the spec/acceptance pair has a gap; they
  must re-run `/mol:spec` to refine the design.

### 2b. Read the Tasks section

This is your task list for this run. If the section is missing,
refuse to continue and tell the user to re-run `/mol:spec` (a Tasks
section is mandatory).

### 2c. Resume sync — reconcile against the codebase

**Before doing any new work, verify what's already done.** A spec's
checkboxes can drift from reality whenever:

- a previous `/mol:impl` run was interrupted between "make the
  change" and "tick the box";
- the user (or another tool) implemented a task by hand without
  going through `/mol:impl`;
- a refactor on `main` happened to subsume a task.

For every `- [ ]` (unchecked) task, perform a **cheap inspection**
to determine whether the work is in fact already in the repo:

| Task shape (verbatim from spec) | Inspection |
|---|---|
| "Write failing tests for X" / "Add tests covering Y" | grep for the test names; if found, run `$META.build.test_single` on them. Pass = done. |
| "Implement X in `<file>`" / "Add `<symbol>` to `<module>`" | `Glob` the file, `Grep` the symbol. Reachable from a non-test caller = done. |
| "Add new `<type/field/route>` `<name>`" | symbol/file existence check at the named location. |
| "Wire X into Y" | grep for the wire-up call site (e.g. `Y.register(X)` / import + use). |
| "Update docstrings via documenter" | spot-check 2–3 named symbols against `$META.doc.style`'s required sections. |
| "Run full check + test suite" | leave unchecked — Step 6 will re-run anyway. |
| Anything you cannot verify cheaply | leave unchecked. **Do not guess. Do not auto-tick on weak evidence.** |

Show the user a one-line-per-task verdict before writing anything:

```
[done — verified]      Implement Foo in src/foo.py        ← will tick
[done — verified]      Add type Bar in src/types.py       ← will tick
[no evidence]          Wire Bar into Service              ← leave
[ambiguous]            Update docs for Baz                ← leave (note why)
```

Wait for user confirmation. After approval, replace `- [ ]` with
`- [x]` for the verified tasks **in one batch** — this is the only
place in `/mol:impl` where batch ticking is allowed (every other
tick is one-at-a-time after the actual work).

Report concisely: *"`<spec-slug>`: 3 of 7 tasks already done;
resuming from 'Wire Bar into Service'."* If 0 tasks need ticking,
say *"no out-of-band progress detected; starting from the top."*
If **all** tasks are already `[x]` after the sync, skip ahead to
Step 6 (verify) and then Step 7 (close-out).

### 2d. Promote status

Update the spec frontmatter to `status: in-progress` (no-op if
already in-progress) before starting Step 3.

If at any later step the spec turns out to be wrong (a task is
infeasible as written, the design has a gap), stop and re-invoke
`/mol:spec` for a supersede/refine. That skill will update the
spec body and recompute the Tasks list (unchecking, removing, or
adding items as needed). Resume with the new task list — Step 2c
runs again on the recomputed list.

## Step 3 — Architecture check

Read the section named by `$META.arch.rules_section` from CLAUDE.md.
Find the closest existing pattern in the codebase:

- `layered` — grep for a module that imports only from allowed layers.
- `crate-graph` — grep workspace `Cargo.toml` for the target crate's
  deps.
- `backend-pillars` — grep the relevant backend subtree for a sibling.
- `package-tree` / `monorepo` — glob the target package for a peer.

For LARGE scope, delegate to the `architect` agent for full
validation before any test is written.

## Code quality rules (apply through Steps 4–6)

- **Type safety.** Every line of code you write — production or test —
  must satisfy the project's static type checker (`mypy --strict` /
  `tsc --strict` / `cargo check` / etc., per `$META.build.check`).
  Forbid escape-hatch top types: `any` / `unknown` (TypeScript),
  `Any` and untyped function signatures (Python), `interface{}` /
  bare `any` (Go), `dyn Any` (Rust). Replace with an explicit union,
  generic, or trait/protocol bound. The only allowed exception is
  the moment of deserialization at a system boundary; narrow
  immediately to a typed shape before passing further inland.

## Step 4 — TDD (RED)

Find the first **Write failing tests …** task in the spec. Delegate
to the `tester` agent:

- Write failing tests in the location `$META.arch.style` dictates.
- Required categories: happy path, edge cases, immutability (if the
  project documents immutable data flow), domain validation (if
  `$META.science.required`).
- Run `$META.build.test_single` (or `build.test`) and confirm tests
  fail for the right reason.

When the tests are written and verified failing, **tick the
corresponding checkbox in the spec file** by replacing `- [ ]` with
`- [x]` on that line. Do this immediately — do not batch ticks.

## Step 5 — Implement (GREEN), one task at a time

For each remaining unchecked task in the spec:

1. Make the change required by that task.
2. Run `$META.build.test` (or the relevant subset) and confirm green
   for the affected behavior.
3. Keep changes inside the layer identified in Step 3.
4. **Tick that task's checkbox in the spec file** before moving to
   the next task.

If a task cannot be done as written — the spec is incomplete or
wrong — stop and re-invoke `/mol:spec` to update the spec via the
supersede/refine flow. Resume with the recomputed task list.

For MEDIUM / LARGE, after the implementation tasks are checked off,
re-delegate to the `architect` agent for the post-impl layer check.
If a corresponding task ("Architecture re-check" or similar) exists
in the spec, tick it.

## Step 6 — Verify

Run in parallel:

- `$META.build.check` (format/lint)
- `$META.build.test` (full suite)

For MEDIUM / LARGE, additionally delegate to the `documenter` agent
to add or update docstrings in the style named by `$META.doc.style`.
Tick the docs task in the spec when complete.

Tick the **Run full check + test suite** task (or equivalent) once
both commands are green.

## Step 7 — Close out the spec

Re-read the spec **and** `{$META.specs_path}{slug}.acceptance.md`. Check three
conditions:

1. Every task in the Tasks section is `[x]`.
2. The latest `$META.build.check` and `$META.build.test` runs were
   both green.
3. Every acceptance criterion with `type ∈ {code, runtime}` has a
   green test path traced in Step 2a-bis. (Other types are handed
   off to runtime evaluators below; they do not block close-out.)

If all three conditions hold:

1. Mark spec `status: done` in the frontmatter.
2. **Auto-commit on close-out (every spec, every scope).** Invoke
   `/mol:commit` (which gates on `/mol:ship commit`) before
   deleting any spec artifacts. Use a conventional-commit message:

   ```
   feat(<scope>): <one-line summary> (<slug>)
   ```

   `<scope>` derives from the spec's primary layer; the summary
   is the first sentence of the spec's Summary section, trimmed
   to fit. For chained sub-specs (`<base>-<NN>-<phase>`), this
   is exactly the per-stage checkpoint required by the
   large-spec split rule (`plugins/mol/rules/large-spec-split.md`)
   — one commit per sub-spec, no bundling.

   If `/mol:commit` reports BLOCK, **do not delete** the
   spec/acceptance/INDEX entry — leave the spec `in-progress`,
   surface the failure, and stop. The user fixes it and re-runs
   `/mol:impl`; Step 2c resume sync recovers.

   Never push, never PR — that is `/mol:push` / `/mol:pr`.
3. **Surface deferred runtime criteria** before deletion. List every
   acceptance criterion whose `type` ∈ {`ui_runtime`, `scientific`,
   `performance`, `docs`}, grouped by the suggested
   `evaluator_hint`. Example:

   ```
   3 criteria deferred to runtime evaluators:
     ui_runtime  → run `/mol:web <slug>`
       - ac-004 — first paint of project tree under 200ms
       - ac-005 — error toast appears on save failure
     performance → no evaluator skill registered; verify by hand
       - ac-007 — list endpoint p95 < 50ms
   ```

   Do **not** auto-invoke. Orchestration is the user's call (or
   their external orchestrator's call); see
   `plugins/mol/rules/evaluator-protocol.md`.
4. Tell the user concisely: *"<slug> code is complete. Deleting
   spec + acceptance + INDEX entry. Runtime evaluators above are
   yours to invoke."*
5. Delete `{$META.specs_path}{slug}.md`.
6. Delete `{$META.specs_path}{slug}.acceptance.md` if present.
7. Remove the entry for `{slug}` from
   `{$META.specs_path}INDEX.md`.
8. If anything from the spec is non-obvious context worth keeping
   (an unusual design choice, a workaround for a hidden constraint,
   a tolerance the user picked deliberately), suggest the user run
   `/mol:note` to capture it. Don't capture it automatically — the
   user decides what's worth keeping.

For chained features, after a successful close-out, **do not auto-
advance to the next sub-spec**. Exit cleanly so the user can
inspect the stage commit before invoking `/mol:impl <base>-NN+1-
<phase>`.

If a task is unchecked OR the verify suite is failing OR a
code/runtime criterion has no green test path:

1. Leave `status: in-progress`.
2. Do **not** delete the spec or the acceptance file.
3. Report the unchecked tasks, the failing checks, and the unmet
   criteria to the user as the next handoff.

## Step 8 — Summary

One line summarizing: scope, files changed, tests passing, spec
status (deleted on completion / N tasks remaining).

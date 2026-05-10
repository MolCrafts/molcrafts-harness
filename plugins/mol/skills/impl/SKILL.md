---
description: Implementation workflow — scope, optional litrev, spec, **acceptance gate** (refuse to start unless `<slug>.md` is `status: approved` AND `<slug>.acceptance.md` exists), **resume sync** (detect tasks already done out-of-band and reconcile checkboxes before doing new work), architecture check, TDD, implement, verify. Reads the spec's Tasks checklist and the acceptance contract; ticks each box as work completes; flips every `code` / `runtime` acceptance criterion to `status: verified` at close-out; parks the spec at `status: code-complete` if runtime-typed criteria are still `pending` (waiting on `/mol:web` etc.) and only deletes the spec + acceptance + INDEX entry once every criterion is `verified`. Writes code, tests, docs; edits the spec file (checkboxes + status) and `acceptance.md` (status fields only). Reads mol_project frontmatter from CLAUDE.md.
argument-hint: "<feature description or path to spec file>"
---

# /mol:impl — Implementation

Read CLAUDE.md. If the first block is a `mol_project:` frontmatter,
parse it; otherwise print the adoption hint and stop. Let `$META`
refer to the parsed frontmatter throughout.

Read `$META.stage` (default: `experimental` if absent — emit the
warning from `plugins/mol/rules/stage-policy.md`). Print one line:
`[mol] stage: <value>`. This skill exposes only two stage hooks
itself; every other stage decision (legacy deletion, deprecation-
shim proposal, dead-code cleanup) is delegated to `/mol:simplify`
at Step 6.5, which is the **single backward-compat gatekeeper**
per `plugins/mol/rules/stage-policy.md`:

- **Pre-work gate**: `maintenance` refuses unless the spec
  frontmatter has `kind: bugfix`. Print the refusal message from
  the rule doc and stop.
- **Commit-message decoration** (`beta` only): the Step 7 auto-
  commit body must include a one-paragraph migration note when
  the diff modifies a public signature.

This skill never decides "delete legacy / preserve as shim /
leave alone" directly — those are all `/mol:simplify`'s call,
made on the diff produced by Steps 4–6.

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
- `status: code-complete` — code is already done; the spec is
  parked waiting for runtime evaluators to flip the remaining
  criteria. **Skip Steps 1–6 entirely** and jump to Step 7's
  finalize check: re-read every criterion's `status`. If all
  are `verified`, advance to `done` and run the close-out
  deletion path. If any non-`code`/`runtime` criterion is still
  `pending`, list them with their `evaluator_hint` and exit
  cleanly (the user runs the named evaluator; this skill is not
  an orchestrator). If a `code`/`runtime` criterion has somehow
  reverted to `pending` (impl was modified out-of-band), drop
  back to `in-progress` and continue from Step 2c so resume sync
  reconciles.
- `status: done` — Step 7 should have already deleted this spec.
  Warn the user and stop; let them either delete the spec by hand
  or open a new one with `/mol:spec`.

### 2a-bis. Acceptance contract gate (HARD)

Read `{$META.specs_path}{slug}.acceptance.md`. If absent, refuse —
tell the user the spec was approved without an acceptance file
(this should be impossible from `/mol:spec`, so it means manual
tampering or a partial supersede). Either restore the file from
git or re-run `/mol:spec <slug>` to regenerate it.

Parse the `criteria:` list from the frontmatter. Each criterion
carries a `status:` field per
`plugins/mol/rules/evaluator-protocol.md` (`pending` / `verified`
/ `failed`; default `pending`). This is the binding "done"
contract for the rest of this run:

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

Display the current ledger before doing any new work so the
user (and you) know where this spec stands:

```
acceptance ledger:
  ac-001 (code)        verified   ← skip during Step 5–7 trace
  ac-002 (code)        pending
  ac-003 (runtime)     pending
  ac-004 (ui_runtime)  pending    → /mol:web <slug> ac-004 after close-out
  ac-005 (performance) failed     → /mol:fix or /mol:spec to refine
```

`code` / `runtime` criteria already at `verified` are not re-
traced; trust the prior verdict unless Step 2c resume sync
finds the underlying test path missing or red, in which case
drop the criterion back to `pending` and re-trace.

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

## Step 6.5 — Hygiene & backward-compat (mandatory)

Invoke `/mol:simplify` on the file list touched in Steps 4–6
(pass it explicitly as `$ARGUMENTS` so `simplify` doesn't re-derive
scope from `git diff`). This step is **mandatory for every spec,
every scope, every stage** — `/mol:simplify` is the single
gatekeeper for backward-compat per
`plugins/mol/rules/stage-policy.md`, and decides:

- whether legacy code newly orphaned by this diff is deleted
  (`experimental`), preserved as a deprecation shim (`stable`),
  flagged for migration-note (`beta`), or left untouched
  (`maintenance`);
- whether dead imports / debug residue / commented-out code
  introduced or revealed by this diff are removed.

`simplify` runs its own build/test gate and reverts the batch on
regression. If revert happens:

1. Leave the spec `status: in-progress`.
2. Do **not** advance to Step 7.
3. Surface the suspected trigger to the user and stop.

The user resolves and re-runs `/mol:impl`; Step 2c resume sync
recovers.

If `simplify` reports manual handoffs (`/mol:refactor`) or rule-
capture suggestions (`/mol:note`), carry them into Step 7 close-
out as advisories — they do not block close-out.

If a "Hygiene cleanup" or equivalent task exists in the spec, tick
it. If not, add one line to the spec's Tasks section recording
that simplify ran clean (so the spec is self-documenting that
backward-compat was reviewed).

## Step 7 — Close out the spec

Re-read the spec **and** `{$META.specs_path}{slug}.acceptance.md`.

### 7a. Update the acceptance ledger

For every criterion with `type ∈ {code, runtime}`, write back its
verdict to `acceptance.md` (the one carved-out exception in
`plugins/mol/rules/evaluator-protocol.md` § *Field semantics*):

- `status: verified` if the criterion's traced test path was
  green in the Step 6 run (or in Step 2a-bis if it was already
  marked `verified` and resume-sync confirmed the path is still
  green).
- `status: failed` if the traced path is red.
- Set `last_checked: <today's ISO date>` alongside.

Do **not** touch criteria with `type ∈ {ui_runtime, scientific,
performance, docs}` — those flip status only when their runtime
evaluator runs. Their existing `status` (almost always `pending`
on first close-out) is left as-is.

### 7b. Decide the next status

Check three conditions:

1. Every task in the Tasks section is `[x]`.
2. The latest `$META.build.check` and `$META.build.test` runs were
   both green.
3. Every acceptance criterion with `type ∈ {code, runtime}` is now
   `status: verified` (no `failed`, no `pending`).

If any of the three fails, leave spec `status: in-progress` and
go to the failure branch at the bottom of this step.

If all three hold, branch on the runtime-typed criteria:

- **No runtime-typed criteria, OR all of them already
  `verified`** → advance directly to `status: done`. Run the
  close-out path below (commit + delete artifacts).
- **At least one runtime-typed criterion is still `pending` or
  `failed`** → set spec `status: code-complete`. **Do not commit
  via `/mol:commit` and do not delete spec / acceptance / INDEX
  artifacts** — the spec is parked waiting for runtime
  evaluators. Surface the deferred list (see *Surface deferred
  runtime criteria* below) and exit cleanly. The user's next
  step is to invoke each named evaluator; on the next
  `/mol:impl <slug>` (or via a future `/mol:close <slug>`),
  Step 2a's `code-complete` branch re-runs this 7b check and
  advances to `done` if the evaluators flipped everything to
  `verified`.

### 7c. Done path (only when status flips to `done`)

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
3. Tell the user concisely: *"<slug> done — every criterion
   verified. Deleting spec + acceptance + INDEX entry."*
4. Delete `{$META.specs_path}{slug}.md`.
5. Delete `{$META.specs_path}{slug}.acceptance.md` if present.
6. Remove the entry for `{slug}` from
   `{$META.specs_path}INDEX.md`.
7. If anything from the spec is non-obvious context worth keeping
   (an unusual design choice, a workaround for a hidden constraint,
   a tolerance the user picked deliberately), suggest the user run
   `/mol:note` to capture it. Don't capture it automatically — the
   user decides what's worth keeping.

### 7d. Code-complete path (runtime evaluators still pending)

When 7b decided `status: code-complete`:

1. Mark spec `status: code-complete` in the frontmatter (keep
   acceptance.md as-is — runtime evaluators will mutate the
   `status:` fields they handle).
2. **Auto-commit the code work.** Invoke `/mol:commit` for the
   code change exactly as in the done path above (same
   conventional-commit message). The commit's existence is what
   makes runtime verification meaningful — evaluators run
   against the committed state, not a dirty tree. If
   `/mol:commit` reports BLOCK, drop back to
   `status: in-progress` and stop (matches the done-path BLOCK
   handling).
3. **Surface the still-pending runtime criteria**, grouped by
   `evaluator_hint`:

   ```
   <slug>: code-complete. 3 criteria still pending verification:
     ui_runtime  → run `/mol:web <slug>`
       - ac-004 — first paint of project tree under 200ms
       - ac-005 — error toast appears on save failure
     performance → no evaluator skill registered; verify by hand
       - ac-007 — list endpoint p95 < 50ms

   Re-run `/mol:impl <slug>` after the evaluators have flipped
   each criterion to `status: verified` to advance the spec to
   `done`.
   ```

   Do **not** auto-invoke. Orchestration is the user's call —
   see `plugins/mol/rules/evaluator-protocol.md`.
4. Do **not** delete spec / acceptance / INDEX entry. The
   acceptance file MUST stay alive for the evaluators to read
   and update.

For chained features, after either close-out path lands its
commit, **do not auto-advance to the next sub-spec**. Exit
cleanly so the user can inspect the stage commit before invoking
`/mol:impl <base>-NN+1-<phase>`.

### 7e. Failure branch

If 7b's three conditions did not all hold (a Tasks item is
unchecked, the verify suite is failing, OR a `code`/`runtime`
criterion is `failed` / `pending` after 7a):

1. Leave `status: in-progress`.
2. Do **not** delete the spec or the acceptance file.
3. Report the unchecked tasks, the failing checks, and the unmet
   (`pending` / `failed`) criteria to the user as the next
   handoff. The acceptance ledger from Step 2a-bis (now updated
   by 7a) is the canonical "where this spec stands" view; print
   it again here.

## Step 8 — Summary

One line summarizing: scope, files changed, tests passing, the
spec's resulting `status:` (`done` → deleted; `code-complete` →
parked with N runtime criteria pending; `in-progress` → N tasks
remaining), and the acceptance-ledger tally (e.g. *"3 verified,
1 failed, 2 pending"*).

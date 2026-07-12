---
description: "Advance a `code-complete` spec to `done` and delete it. Default mode re-checks the acceptance ledger and closes if every criterion is already `status: verified` (the common path after `/mol:bench` or `/mol:web` has run). With `--manual`, the operator asserts the remaining pending criteria are observably met outside the harness (e.g. when `mol_project.bench.repo` is not configured); the skill flips them to `verified` with an audit note, advances to `done`, and deletes spec + acceptance + INDEX entry."
argument-hint: "<spec-slug> [--manual]"
---

# /mol:close — Spec Closer

The closing counterpart to `/mol:impl`. `/mol:impl` parks specs at
`code-complete` when runtime-evaluator-typed criteria
(`scientific` / `performance` / `docs`, plus legacy `ui_runtime`)
are still `pending`. `/mol:close` finishes the job: re-checks the
ledger, advances to `done`, deletes the spec artifacts.

Auto-invoked (default mode) by `/mol:impl` § 4d and `/mol:impl-all`
§ 2c after every finished spec; also runnable standalone. `--manual`
is operator-only — never reached automatically.

Two modes:

- **default** — assume `/mol:bench`, `/mol:web`, or another evaluator
  has already flipped the remaining criteria to `status: verified`.
  Re-read the acceptance file, confirm, advance.
- **`--manual`** — the operator asserts they have observed the
  remaining criteria true outside the harness (e.g. for a project
  where `mol_project.bench.repo` is not configured, or for `docs`
  criteria that a human verifies by reading). Flip all `pending`
  criteria to `verified` with an explicit audit note, then advance.

---

## 1. Pre-flight

Read `CLAUDE.md` → parse `mol_project:` (`$META`); else emit adoption
hint and stop. Print `[mol] stage: <value>`.

Resolve `<slug>` to `{$META.specs_path}{slug}.md` +
`{$META.specs_path}{slug}.acceptance.md`. Refuse if either missing.

**Status gate:**

- `draft` / `approved` → refuse: "spec has not been implemented; run
  `/mol:impl <slug>` first".
- `in-progress` → refuse: "spec is in mid-flight; finish `/mol:impl
  <slug>` first".
- `code-complete` → proceed.
- `done` → no-op: "spec is already done; should already have been
  deleted by `/mol:impl`" (warn and stop; let the operator
  investigate why a `done` spec persisted).

Parse `criteria:` from acceptance frontmatter. Categorise:

- **A** = criteria already `status: verified`.
- **B** = criteria `status: pending` that `/mol:close` may legitimately
  promote in **default** mode — i.e. criteria whose `pass_when` is
  re-checkable here and now (`type: code` with a regex / file existence
  / command exit check; `type: runtime` whose test still passes).
- **C** = criteria `status: pending` that need the operator's manual
  attestation (everything else — `performance`, `scientific`,
  `ui_runtime`, `docs`).

---

## 2. Default mode — `/mol:close <slug>`

Walk **B** criteria first: re-evaluate each `pass_when` literally. If
the condition still holds, flip to `status: verified`; if it now
fails, flip to `status: failed` — both per
`plugins/mol/rules/evaluator-protocol.md` § *Ledger write-back*. On a
failure, print it and **abort** (the spec is broken; do not advance
to `done` until the operator fixes it).

If after **B** is processed all criteria are `verified` (i.e. **C**
is empty), proceed to § 4 (Advance to done).

If **C** is non-empty, print:

```
Spec is parked at code-complete with N criteria still pending external
verification:

  ac-XXX  type: <T>  evaluator: </mol:bench|/mol:web|human>
          <one-line summary>

These criteria require their owed evaluator (or human review) to flip
status: verified. Options:

  1. Run the named evaluator and re-run `/mol:close <slug>`.
  2. Assert manually (you have observed the pass_when condition
     externally) — re-run with `--manual`.
```

Exit without writing anything. Do not advance status.

---

## 3. Manual mode — `/mol:close <slug> --manual`

For each criterion in **C**:

1. Print the criterion's `id`, `summary`, and full `pass_when` block.
2. Flip `status: pending` → `status: verified` per
   `plugins/mol/rules/evaluator-protocol.md` § *Ledger write-back*,
   including its `--manual` extension — `verified_by: human` beside
   `last_checked` — so the audit trail distinguishes
   human-asserted-met from machine-checked-met.

Then proceed to § 4.

`--manual` is opt-in for a reason: it asserts subjective conditions
without machine evidence. Use only when you have actually observed
the `pass_when` condition true in the working tree, an artifact, or
an external run.

---

## 4. Advance to done + delete

When every criterion in the acceptance file is `status: verified`:

1. Flip the spec's frontmatter `status:` to `done` and
   `last-updated:` to today. (Tiny diff; mostly bookkeeping for git
   log.)
2. Invoke `/mol:commit`. The commit message follows the form:

   ```
   chore(<scope>): close <slug> — <N> criteria verified

   <If --manual was used, list the criteria flipped by manual
   attestation, one per line with their pass_when text. Otherwise
   list which criteria default-mode re-checked.>

   Spec + acceptance + INDEX entry deleted on close per
   evaluator-protocol §Acceptance lifecycle.
   ```

   `<scope>` is the spec's top-level project label
   (mol_project.name) or, for chained specs (`<base>-<NN>-<phase>`),
   `<base>`.

3. After the commit succeeds, delete:
   - `{specs_path}{slug}.md`
   - `{specs_path}{slug}.acceptance.md`
   - the matching line in `{specs_path}INDEX.md` (or convert the line
     to a `[closed YYYY-MM-DD]` annotation if the project policy is
     to keep the history visible — default is delete)
   - the `{specs_path}{slug}.artifacts/` directory if it exists
4. Stage the deletions and amend the commit (single atomic close).

If `/mol:commit` BLOCKs (lint / test / format gate fails), do **not**
delete anything. Leave the spec at `code-complete` (revert the
frontmatter flip), print the gate failure, and stop.

---

## 5. Output

One line:

```
[mol:close] <slug> — N criteria verified (M by default check, K by
manual attestation), spec + acceptance + INDEX entry deleted in
commit <sha>.
```

---

## Guardrails

- **Refuse to bypass `/mol:impl`.** Never close a spec from `approved`
  / `in-progress`; the work must have actually happened first.
- **No silent promotion.** `--manual` requires the literal flag; the
  default mode never flips `pending → verified` for criteria
  /mol:close can't re-check.
- **Atomic with the commit.** Spec deletion and frontmatter flip are
  in the same commit so a rollback (or a failed gate) does not leave
  the tree in a half-closed state.
- **No source code changes.** /mol:close only writes to the spec /
  acceptance / INDEX files. If a default-mode re-check reveals
  the code has regressed (a previously-verified criterion now fails),
  abort and tell the operator to run `/mol:fix <slug>`.
- **Pair with `/mol:bench` / `/mol:web` when possible.** Manual close
  is the last-resort path for projects without a configured
  evaluator. The intended flow is `/mol:impl` → owed evaluator
  → `/mol:close`.

---
description: Backward-compat gatekeeper + hygiene cleanup for the current diff, behavior-preserving under a test gate. Auto-invoked by `/mol:impl` Step 6.5; also runnable standalone after `/mol:review` to clean up dead code, magic numbers, and stage-appropriate legacy.
argument-hint: "[path or list of files]"
---

# /mol:simplify — Apply Hygiene Cleanup

Read CLAUDE.md → parse `mol_project:` (`$META`). Read `$META.stage` (default `experimental`). Print `[mol] stage: <value>`.

Write-mode counterpart to `janitor` (read-only). See `plugins/mol/rules/agent-design.md` § "Producer vs reviewer".

## Stage gate (per `plugins/mol/rules/stage-policy.md`)

- `maintenance` — only: dead-import removal, debug-residue deletion, stale-`TODO` deletion *iff* the marker references already-removed code. Naming-drift / magic-literal / constant-extraction → `[skipped — stage: maintenance]`.
- `stable` — refuse to delete anything still referenced by `@deprecated` / `# DEPRECATED` (deprecation must run one full major version first).
- `beta` / `experimental` — full scope contract.

## Scope contract

**Apply** (provably behavior-preserving):

- delete unused import / unreachable branch / unused local
- delete commented-out code
- delete debug `print` / `console.log` / `dbg!`
- inline a magic literal with a named constant **already defined in the file** (no new constants)
- rename a local symbol per captured naming rule (e.g. `natoms` → `n_atoms`) **only** when local to one file and grep confirms no external caller
- whitespace / import-order fixes the formatter missed
- run the language-canonical formatter in fix mode on touched files, and auto-fix lints, per the table in `plugins/mol/agents/janitor.md` § *Language-canonical toolchains* — in scope only when mechanical and behavior-preserving; the Step 5 test gate is the safety net
- delete stale `TODO` / `FIXME` whose reference is dead code

**Refuse** (surface as "manual"):

- copy-paste duplication extraction → `/mol:refactor`
- function-too-long splits → `/mol:refactor`
- public-API renames → `/mol:refactor` with `pm` agent pre-check
- any finding `→ defer to <agent>` from `janitor`
- any finding without a captured rule citation → user runs `/mol:note` first; future run picks it up

## Procedure

### 1. Determine scope

- `$ARGUMENTS` if given, else `git diff --name-only`.
- If the working tree has unrelated uncommitted changes → **stop**, ask user to commit/stash. This skill needs a clean diff to revert cleanly on regression.

### 2. Snapshot test gate

Run `$META.build.check` and `$META.build.test`. Record passing list + pre-existing failures. Revert criterion is "no new failures vs snapshot," not "all green." If `$META.build.test` is already failing in unrelated ways, ask user before proceeding.

### 3. Delegate to `janitor`

Invoke `janitor` agent on Step 1 scope. Capture findings + rule-capture suggestions + deferred-to-other-agent items verbatim.

### 4. Triage findings

For each finding:

- matches **apply** list → candidate for batch apply
- matches **refuse** list → label `manual: route to /mol:refactor (or /mol:fix)`, skip
- if `janitor` left a `Fix:` line → propose that exact patch. Multi-line / file-level reorg → out of contract, skip.

Show triage table:

```
[apply]    src/foo.py:42  unused import os               → delete line
[apply]    src/foo.py:88  debug print() residue          → delete line
[apply]    src/bar.ts:17  literal "#fff"                 → replace with TOKENS.surface (already in scope)
[manual]   src/baz.py:12  function 142 lines             → /mol:refactor (split)
[manual]   src/baz.py:55  copy-paste of foo.py:120-140   → /mol:refactor (extract)
[skipped]  src/qux.py:9   naming drift (no captured rule)→ /mol:note first, then re-run
```

Wait for explicit user approval. User may de-select any `[apply]` row.

### 5. Apply, verify, revert on regression

1. Apply minimal patch per finding (one Edit each when possible).
2. After **whole batch**, run `$META.build.test`.
3. If any Step-2-green test is now red → **revert entire batch** (`git checkout -- <files>`), tell user which finding was the suspected trigger. (Bisect is user's call.)
4. If green: run `$META.build.check`, then **run the language-canonical trio explicitly** even when `build.check` skips one — commands per the table in `plugins/mol/agents/janitor.md` § *Language-canonical toolchains*. Non-zero from any = test regression: revert batch, surface failing tool. At `maintenance` the trio is verify-only (no fix-mode formatter, no `--fix`).

Never partial-apply. Green-after-revert is the only acceptable failure mode.

### 6. Report

```
/mol:simplify: applied N hygiene fixes across K files
  - N_unused imports / debug residue / commented code
  - N_naming drift fixes (captured rules)
  - N_token-or-constant substitutions

Manual handoffs (M):
  - <finding> → /mol:refactor / /mol:fix
Suggested rule captures (S):
  - <suggestion> → /mol:note
```

Surface rule-capture suggestions separately — user decides which become rules.

End with a one-line summary: files touched, fixes applied, manual handoffs queued, tests still green.

## Guardrails

- **Behavior-preserving only.** Runtime/API/test-outcome changes → `/mol:fix` or `/mol:refactor`.
- **Whole-batch atomicity.** Regression reverts entire batch — no half-cleaned tree.
- **No new abstractions.** Only delete or rename. No new helpers / constants / modules.
- **No CLAUDE.md / `.claude/notes/` writes.** Rule capture is `/mol:note`'s job.

## Idempotency

Second run on same scope finds zero `[apply]` candidates; reports zero changes or re-surfaces the first run's manual / rule-capture handoffs.

## When to invoke

- **Mandatory from `/mol:impl`** — Step 6.5 invokes this on the impl diff before close-out commit. Single point where per-stage backward-compat is enforced (legacy delete vs shim vs leave alone). User cannot opt out, but may de-select `[apply]` rows in Step 4.
- **Standalone** — after `/mol:review` flagged hygiene findings, or as periodic cleanup on the current uncommitted diff.

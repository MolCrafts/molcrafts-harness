# Large-Spec Split Rule

**A spec that an agent cannot implement well in one shot is a bug,
not a feature.** Long specs degrade: tests drift from intent, partial
work piles up unstaged, and the agent loses the thread between the
first task and the last. This rule is the harness's response: detect
"large" at spec-writing time and force a deterministic split — without
consulting the user — into a chain of ordered, small, individually
shippable sub-specs. Each sub-spec gets its own branch checkpoint
(via a stage commit), so the chain is reviewable mid-flight and
recoverable on interrupt.

This rule is **non-negotiable**. Skills do not prompt the user before
applying it. The user can override by editing or deleting sub-specs
afterward; that's recovery, not approval.

## What counts as "large"

`spec-writer` MUST return `Status: split-needed` if **any** of:

- **Task count.** The drafted Tasks list has more than **10** atomic
  items. (The earlier "~12" guidance is replaced by 10. The lower
  bound 4 is unchanged.)
- **Cross-layer reach.** The Files-to-create-or-modify list spans
  more than one architectural layer / package / crate per
  `$META.arch.style`. (Two layers ⇒ split.)
- **New top-level concept.** The spec introduces a new driver,
  package, frame field, layer, or any "LARGE" item per the
  `/mol:impl` Step 1 scope ladder. LARGE scope and a single spec
  are mutually exclusive.

A draft can trigger more than one of these — that just means the
proposed cut needs more parts.

## How the cut is shaped

The proposed cut is an **ordered chain** of sub-specs, each itself
a valid spec under this rule (4–10 atomic tasks, single layer,
not LARGE). The numbering is part of the slug so siblings sort:

```
<base-slug>-01-<phase>
<base-slug>-02-<phase>
<base-slug>-03-<phase>
…
```

`<base-slug>` is what the user originally asked for (kebab-case).
`<phase>` is a one-or-two-word verb-shaped tag (`types`, `parser`,
`wire`, `tests`, `docs`) — not a description.

Ordering rule: **each sub-spec must be implementable, testable, and
mergeable on its own**, given that earlier sub-specs in the chain
have landed. No sub-spec may depend on a later sub-spec. This is
what makes per-stage commits meaningful — the tip of the branch is
green at every checkpoint.

A spec-writer that cannot produce such a chain returns
`Status: blocked` instead of an unsound `split-needed`.

## /mol:spec — auto-split, no prompt

When `spec-writer` returns `Status: split-needed` with a proposed
cut, `/mol:spec` MUST:

1. **Not ask the user.** No "do you want to split?" dialogue. The
   rule has already decided.
2. Iterate `spec-writer` once per sub-slug in the chain, feeding
   each invocation the sub-slug, the relevant scope, and a pointer
   to its predecessors so dependencies are explicit.
3. Write each `<sub-slug>.md` + `<sub-slug>.acceptance.md` pair as
   it returns.
4. Add **one entry per sub-slug** to `INDEX.md`, in chain order.
5. Report the chain to the user as a numbered list at the end —
   "spec → 4 sub-specs written; INDEX updated; ready for `/mol:impl
   <base-slug>-01-<phase>`."

The user may still edit, retype, or delete a sub-spec afterward.
That is recovery — not part of the auto-split decision path.

## /mol:impl — auto-branch + per-stage commit

When `/mol:impl` is invoked on a sub-spec whose slug matches the
chain pattern `<base>-<NN>-<phase>` (or on LARGE scope without a
chain — same handling), it MUST:

1. **Open a feature branch automatically.** If the current branch
   is the project default branch (`upstream`'s default, or `main`
   / `master` when no upstream is configured), create and check
   out `feat/<base>` (or reuse it if it already exists and is
   ahead of the default branch). Do not prompt; print one line:
   `/mol:impl: switched to branch feat/<base>`.

   If the current branch already looks like a feature branch
   (anything other than the default), stay on it and skip
   creation — the user has positioned themselves deliberately.

2. **Inherit the baseline auto-commit.** `/mol:impl` already
   commits exactly once on every successful close-out (see Step 7
   of `plugins/mol/skills/impl/SKILL.md`); for a chain, that
   baseline behavior **is** the per-stage checkpoint — one commit
   per sub-spec, no bundling. The chain does not introduce a
   second commit path; it just guarantees the close-out fires N
   times (once per sub-spec) instead of once.

3. **Never push, never PR.** Pushing the branch is `/mol:push`'s
   job, opening the PR is `/mol:pr`'s. The auto-branch + stage
   commits are local-only checkpoints.

The chain is **not auto-advanced**. After committing sub-spec
01, `/mol:impl` exits cleanly; the user invokes `/mol:impl
<base>-02-<phase>` next. (This keeps the user in control of
pacing and lets them inspect each stage commit before the next
sub-spec begins.)

## Why this is a rule, not a preference

- A monolithic LARGE spec produces a single giant commit at the
  end of `/mol:impl` (or, worse, a long-running dirty tree that
  is one interruption away from being thrown out). Per-stage
  commits give a reviewable history and a recoverable failure
  mode.
- Asking the user "should I split?" every time is friction
  without information — the user has no context the harness
  doesn't already have at spec-writing time.
- Asking the user "should I open a branch?" every time is the
  same friction. If they wanted to stay on the default branch,
  they would not be running `/mol:impl` on a feature.

## What this rule does **not** do

- It does not bundle commits across sub-specs. Each sub-spec =
  one commit; merging two sub-specs into one commit would lose
  the checkpoint property.
- It does not auto-push or auto-PR. See `/mol:push` and `/mol:pr`.
- It does not split SMALL or MEDIUM specs. A 6-task single-layer
  spec is fine as-is.
- It does not retroactively split an already-approved monolithic
  spec. If the user wants to break one up, they re-run `/mol:spec`
  with a `supersede:<slug>` decision and the rule fires fresh.

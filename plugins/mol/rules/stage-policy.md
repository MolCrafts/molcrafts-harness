# Project Stage Policy

A project's **lifecycle stage** controls how aggressive the writing
skills (`/mol:impl`, `/mol:fix`, `/mol:refactor`, `/mol:simplify`)
and the static reviewers (`pm`, `janitor`, `architect`) are allowed
to be when they touch existing code. The stage answers one question:
**how much of the existing surface is the harness allowed to break,
delete, or rewrite?**

The stage is declared once, in CLAUDE.md's `mol_project:` frontmatter
(`mol_project.stage`, see `claude-md-metadata.md`). Skills read it
on every run. Changing the stage is an explicit decision the user
makes by editing CLAUDE.md — not something a skill negotiates per
task.

## The four stages

The stage names are the standard software-lifecycle terms; they map
cleanly to semver intent. There are exactly four — anything finer is
not actionable.

| Stage          | Semver intent             | Breaking changes | Legacy code | Deprecation path |
|----------------|---------------------------|------------------|-------------|------------------|
| `experimental` | pre-1.0 / `0.x`           | normal & encouraged | delete on sight | not required |
| `beta`         | pre-1.0 with known users  | allowed at minor bumps with migration note | remove at next minor | one-minor warning, optional |
| `stable`       | `≥ 1.0`, semver applies   | major bumps only | deprecate-then-remove across one major | required, one-major notice |
| `maintenance`  | bug fixes / security only | refused | untouched | n/a (no removals) |

### `experimental` — pre-1.0, churn allowed

The default for a new project, and the right answer until the
public API has been used by anyone who isn't the author.

- Refactors may rename, move, or delete public symbols freely.
- No backward-compat shims, no deprecation warnings, no `# legacy`
  helpers. **Delete legacy code on sight** — keeping it around for
  "just in case" is a `🟡` hygiene finding, not a feature.
- `/mol:impl` may rewrite an existing implementation rather than
  extend it if rewriting produces cleaner code in the same diff
  budget.
- `pm` agent **demotes** breaking-change findings: a removed public
  symbol is `🟢` (informational), not `🚨`.
- `janitor` halves its debt-marker tolerance (`todo_window_days /
  2`) — short-lived projects shouldn't be carrying old `TODO`s.

### `beta` — feature work continues, users exist

The project has external callers but is still pre-1.0 (or the user
has explicitly picked `beta` to mean "1.x with churn budget").

- Breaking changes are allowed at the next minor bump but **must
  include a migration note** in the commit body (one paragraph,
  before/after example).
- `pm` raises an unannounced public removal to `🔴` (down from `🚨`
  at `stable`).
- `/mol:refactor` proceeds with public-API rewrites but the
  `architect` post-check verifies that the README / tutorials still
  compile against the new shape.
- `janitor` uses the default debt window.

### `stable` — semver applies, callers are pinned

The project ships a `1.x` line that downstream code pins to. The
contract is "no breaking changes within a major version."

- `/mol:impl` defaults to **additive** changes. Modifying an
  existing public signature requires either (a) the user explicitly
  acknowledged a major bump, or (b) a deprecation shim that
  forwards the old call to the new one and emits a deprecation
  warning. `/mol:simplify` (mandatorily invoked at `/mol:impl`
  Step 6.5) proposes the shim and pauses for user approval before
  applying — `/mol:impl` itself never decides backward-compat;
  it delegates to `/mol:simplify` as the single gatekeeper.
- `/mol:refactor` may not change public symbol names without first
  passing `pm` review. Internal renames are unaffected.
- `pm` raises any unannounced public removal / rename / re-type to
  `🚨` (this is the existing default).
- `janitor` doubles its debt-marker tolerance (`todo_window_days ×
  2`) — stable projects accumulate longer-lived `TODO`s legitimately
  (waiting on upstream, waiting on a major bump). Stale-marker
  noise is the wrong battle.
- Deletion of legacy / deprecated code is gated: it must have lived
  through one full major version with a deprecation warning before
  removal. `/mol:simplify` refuses to delete anything still
  referenced by a `@deprecated` / `# DEPRECATED` marker.

### `maintenance` — bug fixes only

The project is in long-term support: bug fixes, security patches,
documentation corrections. No new features. No API changes. No
cosmetic refactors.

- `/mol:fix` is the only writing skill that proceeds normally. Its
  scope discipline tightens: a fix may not touch lines unrelated to
  the reproduction, may not introduce new abstractions, and may not
  rename anything (even local symbols) outside the immediate fix
  surface.
- `/mol:impl` **refuses** unless the spec is explicitly marked
  `kind: bugfix` in its frontmatter. Print:
  *"`<project>` is in `maintenance` stage; new-feature specs are
  out of scope. If this is a regression fix, mark the spec
  `kind: bugfix` and re-run."*
- `/mol:refactor` **refuses** outright. Print:
  *"`<project>` is in `maintenance`; refactors are out of scope.
  Bump the stage in CLAUDE.md if this is intentional."*
- `/mol:simplify` only applies the most conservative subset of its
  scope contract: dead-import removal, debug-residue deletion, and
  stale-`TODO` deletion *if and only if* the `TODO` references
  code already removed by an earlier bug-fix commit. Naming-drift
  fixes, magic-literal substitutions, and constant-extraction are
  refused.
- `janitor` reports findings but every entry is downgraded one
  severity tier (🚨 → 🔴, 🔴 → 🟡, 🟡 → 🟢) — the user has
  declared cosmetic noise out of scope until the stage changes.

## Default and graceful degradation

`mol_project.stage` is **optional**. When absent, skills default to
`experimental` and emit a one-line warning on first read:

```
[mol] mol_project.stage not declared; defaulting to `experimental`.
      Set it in CLAUDE.md to govern refactor / breaking-change posture
      (see plugins/mol/rules/stage-policy.md).
```

Why default to `experimental` rather than refusing? Most projects
adopting the harness for the first time *are* pre-1.0. Defaulting
to the most permissive stage matches reality and keeps adoption
friction low. A user with a `1.x` library will notice the warning
and set `stage: stable` once.

## Skill responsibilities at parse time

Every writing skill MUST, immediately after parsing `$META`:

1. Read `$META.stage` (default: `experimental`).
2. Print one line confirming the stage:
   `[mol] stage: <value>`
3. Apply the per-stage rules above for the rest of the run.

Every reviewer agent (`pm`, `janitor`, `architect`) MUST consult
`$META.stage` before assigning severity, so the same finding maps
to different severity at different stages per the matrix above.

## What this rule does **not** do

- It does not replace semver. Semver is the *version* contract; the
  stage is the *behavior* contract for the harness. They reinforce
  each other but are independent declarations.
- It does not gate `/mol:litrev`, `/mol:review`, `/mol:test`,
  `/mol:docs`, `/mol:note`, or any read-only / capture-only skill.
  Those are stage-independent.
- It does not auto-bump the stage. Moving from `experimental` to
  `beta` (or `stable` to `maintenance`) is a deliberate user
  decision recorded in CLAUDE.md, not something the harness infers.
- It does not exempt `/mol:fix` at any stage. A bug is a bug; fixing
  it is always in scope.

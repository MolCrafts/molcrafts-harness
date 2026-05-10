---
description: Upgrade an existing harness to the current mol-agent plugin version's spec — install or repair the mol_project frontmatter to the current contract, refresh managed sections to the current template body, migrate legacy layouts (e.g. .agent/specs/ → .claude/specs/) per the current convention, rebuild drifted spec INDEX, repair orphan stable markers. Surfaces content-level drift (judgement-required) as a manual TODO list. Re-runs /mol-agent:check at the end to confirm convergence. Writes only managed sections, mol_project frontmatter, and approved file moves; never touches user-authored prose.
argument-hint: "[<project-root>]"
---

# /mol-agent:update — Upgrade Harness to Current Version

`/mol-agent:update` brings an already-installed harness **forward to
the version of the mol-agent plugin currently on disk.** The plugin's
own SKILL.md / templates / migration table are the *target state*;
this skill is the migration tool.

```
bootstrap   creates the harness at the current version (no harness exists)
check       reads the harness; reports drift from the current version
update      applies the upgrade — brings the harness to the current version
```

If the repo has no harness yet, this skill will say so and direct
the user to `/mol-agent:bootstrap`. It does not initialize from
scratch.

## What "the current version's spec" covers

The target state is everything the plugin **as it sits on disk
right now** dictates. Concretely:

1. **Frontmatter contract** — `mol_project:` shape per
   `${CLAUDE_PLUGIN_ROOT}/plugins/mol/rules/claude-md-metadata.md`.
   Whatever fields that document currently lists as required — and
   in their current names — are the target.
2. **Managed-section templates** — the `<!-- mol-agent:bootstrap:managed
   begin/end -->` block bodies inside
   `${CLAUDE_PLUGIN_ROOT}/plugins/mol-agent/skills/bootstrap/SKILL.md`.
3. **Layout conventions** — the migration table in this skill (§
   below) names every legacy → current path move that the current
   version expects.
4. **Structural invariants** — every spec under `specs_path/` is
   listed in `INDEX.md` and vice versa; every stable marker has a
   matching close.

Anything outside this list is **content**, not version-spec, and
update does not auto-modify it. Examples of content (always manual
TODO, never auto-fix):

- knowledge embedded in a skill body that should live in CLAUDE.md
- a `.claude/agents/` agent whose axis overlaps another's
- a contract document misplaced under `docs/`
- a spec body that is internally inconsistent
- a `status: done` spec still on disk (deletion contract belongs to
  `/mol:impl` § 7, which has the conditions to verify before
  deletion)

These need user reasoning. Update will surface them faithfully (as
they came out of `/mol-agent:check`) but never act on them.

## Migration table (current-version layout)

| From (legacy)               | To (current)         | Why |
|-----------------------------|----------------------|-----|
| `.agent/specs/`             | `.claude/specs/`     | active vs passive split (pre-v0.3.0 convention; specs are runtime artifacts) |
| `docs/decisions/`           | `.claude/notes/decisions/`  | internal context, not public docs |
| `docs/contracts/`           | `.claude/notes/contracts/`  | internal context |
| `docs/agent-rubrics*.md`    | `.claude/notes/rubrics/`    | internal context |
| `.claude/NOTES.md`          | `.claude/notes/notes.md`    | passive memory belongs in `.claude/notes/`, not at `.claude/` root |
| `.agent/notes.md`           | `.claude/notes/notes.md`    | v0.3.0: passive context folder folds into `.claude/notes/` per Claude Code's spec (no native top-level `.agent/`); name avoids collision with `.claude/agents/` (Claude Code's agent definitions) |
| `.agent/architecture.md`    | `.claude/notes/architecture.md` | v0.3.0 |
| `.agent/decisions/`         | `.claude/notes/decisions/`  | v0.3.0 |
| `.agent/rubrics/`           | `.claude/notes/rubrics/`    | v0.3.0 |
| `.agent/contracts/`         | `.claude/notes/contracts/`  | v0.3.0 |
| `.agent/debt/`              | `.claude/notes/debt/`       | v0.3.0 |
| `.agent/handoffs/`          | `.claude/notes/handoffs/`   | v0.3.0 |
| `.agent/open-questions.md`  | `.claude/notes/open-questions.md` | v0.3.0 |
| `.agent/README.md`          | `.claude/notes/README.md`   | v0.3.0 |
| `mol_project.notes_path: .agent/...` or `.claude/NOTES.md` | `mol_project.notes_path: .claude/notes/...` | v0.3.0: frontmatter follows the path move |
| `mol_project.perf:` block in CLAUDE.md frontmatter | (delete) | `perf.focus` was a single-value enum that didn't scale to multi-facet projects. The `optimizer` agent now detects catalogs per file. |

Add new rows as new conventions are codified — that is how the
"current version's spec" evolves. A layout violation **not** in
this table is content-level drift and goes to manual TODO; do not
invent moves.

## Procedure

### 1. Detect

Confirm a harness is present:

- `CLAUDE.md` exists at the target root
- at least one of `.claude/notes/`, `.claude/specs/` exists

If not, report *"no harness found — run `/mol-agent:bootstrap`
first"* and stop.

Refuse to run on a dirty working tree by default — moves are hard
to review inside a dirty diff. Suggest commit-or-stash and stop;
allow `--allow-dirty` (or an explicit user override in chat) to
proceed.

### 2. Compute the version diff

Build the "current version's expected shape" by reading directly
from the plugin source:

- the frontmatter contract from `claude-md-metadata.md`
- the managed-section template body from `bootstrap/SKILL.md`
- the migration table in § above
- the structural invariants list above

Then walk the harness on disk and produce a **structural diff**:

- frontmatter: missing block / missing required field / stale value
  in a required field / required field renamed
- managed sections: marker missing / drifted body / orphan marker
- layout: any `From (legacy)` path from the migration table that
  exists in the repo
- structural invariants: spec files not in INDEX, INDEX entries
  with no file, unmatched markers

For convenience and DRY, this skill also invokes `/mol-agent:check`
internally and pulls in any **content-level** findings (Layering /
Orthogonality / Knowledge / Capability / Workflow / Idempotency /
anti-patterns) — those become the manual TODO bucket directly. The
structural diff above is the *upgrade plan*; check's content
findings are the *manual TODO list*.

If the structural diff is empty AND check returned zero content
findings, output *"harness already at current version"* and stop.

### 3. Rescan repo (only when frontmatter values are queued)

If the upgrade plan rewrites any `mol_project:` field's value
(e.g. `build.test`), re-run the bootstrap inspection — primary
language, build tool, test runner, formatter, linter, numeric
library use, CI config — to derive the ground-truth value to
write. Compare against the existing frontmatter; record old → new.

Skip this step if no frontmatter values need rewriting (a missing
required field that already has a default, for instance).

### 4. Reach approval

Show the user one combined plan:

```
Upgrade plan (n items, target = current plugin version):
  - install mol_project frontmatter (block missing per current contract)
  - rename mol_project.foo → mol_project.bar (renamed in current contract)
  - refresh CLAUDE.md managed section (template body changed)
  - move .agent/specs/ → .claude/specs/ (current convention)
  - rebuild .claude/specs/INDEX.md (3 files unindexed)

Manual TODO (m content-level items, surfaced from /mol-agent:check):
  🔴 .claude/notes/notes.md — agent contract content here belongs in `.claude/agents/` (rule O3)
  🟡 abc-feature.md — status: done but file still present (rule H; deletion is /mol:impl's job)
  ...
```

If the upgrade plan is empty but the manual list is non-empty,
say *"harness already at current version; m manual TODOs from
content-level review below"* and emit just the manual list.

If both are empty, *"harness already at current version"*.

Otherwise, wait for explicit go-ahead. Allow per-item rejection
(*"yes to frontmatter, skip the move"*).

### 5. Apply

For each approved upgrade item:

- **frontmatter (install)**: write a fresh `mol_project:` YAML
  block at the very top of CLAUDE.md per the current contract.
  Preserve any pre-existing first-line content by moving it below
  the new frontmatter.
- **frontmatter (field rename / repair)**: rewrite only the
  affected fields in the existing block. Preserve fields the
  contract doesn't enforce (user customizations).
- **managed-section refresh**: replace contents between the
  stable markers with the current template body.
- **orphan-marker repair**: only when context is unambiguous;
  otherwise demote to manual TODO at this point.
- **INDEX rebuild**: regenerate INDEX.md from actual spec files.
- **migration**: `git mv` (or `mv`) per the table; patch INDEX
  entries that referenced the old path.

After each apply, report a one-line action log:
`upgraded mol_project frontmatter to current contract`,
`refreshed CLAUDE.md managed section`,
`migrated .agent/specs/ → .claude/specs/`.

### 6. Re-run /mol-agent:check (convergence proof)

Run check on the now-updated harness. Verify:

- the structural drift you applied has disappeared
- no new structural findings were introduced (e.g. by overwriting
  the wrong block)

The manual TODOs are expected to remain — those were content-level
to begin with.

Surface any 🚨 / 🔴 still standing on the structural axis as a bug
in *this* skill (the upgrade plan should have covered them).

### 7. Report

Concise summary:

- upgrade items applied (count + brief list)
- manual TODOs surfaced (count + severity breakdown)
- post-update structural check: clean / not clean
- the suggested next step

If manual TODOs exist, end with:
*"address the manual TODOs and run `/mol-agent:check` to re-verify
content-level cleanliness."*

End with a one-line summary in the standard form (F2).

## Guardrails

- **Do not** rewrite anything outside managed sections, the
  `mol_project:` frontmatter block, or paths approved for
  migration.
- **Do not** invent migrations not in the table. The table *is*
  the version-spec for layout; layout drift outside it is content
  and goes to manual TODO.
- **Do not** delete user-authored notes, decisions, or specs in
  the course of migration. Move them, never drop them.
- **Do not** pad managed sections with content the project
  doesn't have. The template is a ceiling, not a floor.
- **Do not** auto-delete a `status: done` spec — deletion contract
  belongs to `/mol:impl` § 7. Flag as manual TODO.
- **Do not** silently change anything that isn't dictated by the
  current version's spec (frontmatter contract / managed-section
  templates / migration table / structural invariants).
- **Do not** run on a dirty working tree without explicit override.

## Idempotency

Running `/mol-agent:update` repeatedly must converge:

- once the harness is at the current version, output is one line
  and no writes occur
- managed sections are byte-identical after consecutive runs (no
  whitespace churn)
- migrations are one-shot: a file moved once does not re-move
- the post-fix re-check (step 6) is the convergence proof; if it
  still has structural findings after step 5, that is a bug in
  this skill (report it)

## Output format

- During detect: one line — *"harness found"* / *"no harness"* /
  *"dirty tree, aborting (use --allow-dirty to override)"*.
- During version diff: silent count of upgrade items + manual
  TODOs.
- During planning: the two-section plan (Upgrade plan / Manual
  TODO).
- During application: per-item action lines.
- During re-check: any structural findings still standing, or
  *"clean"*.
- Final summary (F2): one line — *N upgraded, M manual TODOs,
  re-check status*.

---
description: Scaffold a new skill inside one of the molcrafts plugins (mol, mol-agent, mol-plugin). Creates the skill directory and a complete, runnable SKILL.md authored end-to-end from the user's description — no TODO placeholders for the user to fill in afterwards. Writes are confined to (a) the new `plugins/<plugin>/skills/<name>/SKILL.md` and (b) appending one row to that plugin's `README.md` skills table; runs `/mol-plugin:check` at the end so the new skill is verified before the procedure exits.
argument-hint: "<plugin:skill-name> [<one-line description>]"
---

# /mol-plugin:new-skill — Skill Scaffold

Scaffold a new skill in this marketplace. Use when adding a verb
that doesn't yet exist — e.g. `mol:bench`, `mol-agent:foo`,
`mol-plugin:audit-templates`.

This skill writes inside
`plugins/<plugin>/skills/<skill-name>/` and appends exactly one
row to `plugins/<plugin>/README.md`'s skills table. It never
touches existing skills, `plugin.json`, or any other metadata.

## Authorship contract

The output of this skill is a **complete, runnable** SKILL.md —
not a stub. Procedure steps are fully authored from the user's
description (and any prior conversational context). `TODO`
placeholders in the procedure body are forbidden: a stub leaves
the user with the same design problem they came in with, just
with a file path attached.

If the description is ambiguous enough that you cannot
confidently author a complete procedure, **ask 1–2 targeted
questions before writing**. Resolve the ambiguity in
conversation, then author. Never resolve ambiguity by emitting
a `TODO`.

## Procedure

### 1. Parse arguments

Argument shape: `<plugin>:<skill-name> [<description>]`.

Validate:

- `<plugin>` is one of `mol`, `mol-agent`, `mol-plugin` (or
  another directory that already exists under `plugins/`).
- `<skill-name>` is kebab-case, no spaces, not already taken.
- Description, if given, is one sentence.

If anything fails validation, report and stop.

### 2. Read a sibling as a structural model

Read one existing SKILL.md under the same plugin to match the
local voice and frontmatter shape. Default models:

- `mol` → `plugins/mol/skills/note/SKILL.md` (mid-complexity,
  writing skill)
- `mol-agent` → `plugins/mol-agent/skills/check/SKILL.md`
  (read-only) or `plugins/mol-agent/skills/update/SKILL.md`
  (writing)
- `mol-plugin` → `plugins/mol-plugin/skills/check/SKILL.md`

Note the structure (not the content): frontmatter
(`description` + `argument-hint`), an H1 with
`/<plugin>:<skill>` heading, a one-paragraph purpose, numbered
Procedure, optional Guardrails, optional Idempotency, Output
format.

### 3. Resolve the design before authoring

From the user-supplied description plus any prior conversation,
extract:

- **Inputs.** What `$ARGUMENTS` parses as. What the skill reads
  from CLAUDE.md / the project. What it ingests from siblings.
- **Behavior.** The decisive verbs (probe? generate? gate?
  delegate? orchestrate?). The branches (success path vs.
  failure path; converge vs. discard; PROCEED vs. BLOCK).
- **Outputs.** Files written, agents invoked, user-facing
  output shape, the one-line F2 summary.
- **Boundaries.** Read-only vs. writing; what the skill
  refuses to touch; how it relates to neighboring skills
  (`/mol:spec` vs `/mol:note`, `/mol:fix` vs `/mol:impl`,
  etc.) so the catalog stays orthogonal.

If any of these four are unclear from the inputs you have,
**ask 1–2 targeted questions** of the user now. Do not write a
file with the gaps in it.

### 4. Author the complete SKILL.md

Produce the full body. Frontmatter:

```markdown
---
description: <one or two sentences captured verbatim from the user's intent; mention read-only vs. writes; mention any sibling-skill relationship that defines the boundary>
argument-hint: "<concrete shape, per /mol-plugin:check Step 3 — e.g. <arg>, [arg], <arg> [<arg>], <a | b | c>>"
---
```

Body shape (numbered Procedure with concrete steps, not
placeholders):

```markdown
# /<plugin>:<skill-name> — <Title>

<one paragraph: what this skill does, when to use it, and how
it differs from the nearest sibling>

## Procedure

### 1. <verb> — <concrete first action>

<what the skill actually does at this step, in prose. No
TODOs. If a branch exists, name both branches.>

### 2. …

## Output format

<the user-facing output shape; the F2 one-line summary at the
end>

## Guardrails

- <real guardrails specific to this skill — read-only?
  refuses to edit X? never auto-loops? — derived from the
  design, not boilerplate>
```

Two integrity rules while authoring:

- **Do not copy another skill's procedure verbatim.** Mirror
  the headings and the frontmatter shape; *author* the
  procedure for this skill's own purpose.
- **Do not invent capabilities the user did not ask for.** A
  scaffolder's job is to capture intent precisely, not to
  expand it. If you find yourself adding a feature the user
  didn't mention, stop and ask first.

### 5. Reach approval

Show the user the path you would create and the **complete**
body. Approval here is for redirection ("change step 3 to
also do X", "drop the discard branch") — not a confirmation
that a stub is acceptable. Do not write before approval.

### 6. Apply

Write the file. Report
`created plugins/<plugin>/skills/<skill-name>/SKILL.md`.

### 7. Register in the plugin README

Append one row to `plugins/<plugin>/README.md`'s skills table.
Read the table first — copy its column shape exactly:

```
| `/<plugin>:<skill-name>` | <one-sentence purpose, mirroring the frontmatter description's first sentence and matching the voice of neighboring rows> |
```

Insert the new row at the bottom of the table, before the next
non-table line. Do not edit any other part of the README — not
the headline, not the workflow block, not the install section.

### 8. Run `/mol-plugin:check`

Invoke `/mol-plugin:check <plugin>` to confirm the new skill
passes structural validation (frontmatter, argument-hint shape,
H1 match, cross-references, README consistency). If it reports
errors, fix them before the procedure exits — the scaffolder is
not done until check is green.

### 9. Suggest release follow-up

If this skill should ship in the next marketplace release, tell
the user to run `/mol-plugin:release patch` and `/mol:tag` when
they're ready. Do not run those — release timing is the user's
call.

End with a one-line summary (F2).

## Guardrails

- **No TODOs in the procedure body.** Reiterated at the
  contract level; this is the rule that distinguishes
  "scaffold" from "stub".
- **Do not** create a skill in a plugin directory that doesn't
  already exist; scaffolding a whole new plugin is a bigger
  decision than this skill is sized for.
- **Do not** copy another skill's procedure body. Frontmatter
  shape and headings are fine to mirror; specific steps must
  be authored.
- **Do not** edit `plugin.json`, `marketplace.json`, or any
  README section other than the skills table. The scaffolder's
  write surface is exactly: the new SKILL.md and one appended
  row in the plugin README's skills table — nothing else.

## Output format

- Validation result: pass or specific failure.
- Resolved design (a 4-bullet recap of inputs / behavior /
  outputs / boundaries) — proves the skill captured intent
  before writing.
- Plan: path + complete body preview.
- Application: `created <path>` plus the one-line README row
  diff.
- `/mol-plugin:check` verdict for the new skill (pass / errors
  fixed / errors remaining).
- Release follow-up prompt: one line, only if applicable.
- Final summary (F2): one line.

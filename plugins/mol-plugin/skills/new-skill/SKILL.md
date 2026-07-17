---
name: new-skill
description: Scaffold one shared Claude-first skill inside a MolCrafts plugin, including Codex-compatible metadata and adapter linkage, without creating a duplicate workflow. Updates the plugin README and runs `/mol-plugin:check`.
argument-hint: "<plugin:skill-name> [<one-line description>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol-plugin:new-skill — Skill Scaffold

Scaffold a new skill in this marketplace (e.g. `mol:bench`, `mol-plugin:audit-templates`).

Write surface: `plugins/<plugin>/skills/<skill-name>/SKILL.md` + one appended row in `plugins/<plugin>/README.md`'s skills table. Reuse the plugin's existing `skills/CODEX.md`; never create a second Codex copy of the workflow. Never touch existing skills, plugin manifests, or marketplace metadata.

## Authorship contract

Output must be a **complete, runnable** SKILL.md — not a stub. Procedure steps fully authored from the user's description. `TODO` placeholders forbidden.

If the description is ambiguous, **ask 1–2 targeted questions before writing**. Never resolve ambiguity by emitting `TODO`.

## Procedure

### 1. Parse arguments

Form: `<plugin>:<skill-name> [<description>]`.

Validate:

- `<plugin>` ∈ `mol`, `mol-plugin` (or another existing dir under `plugins/`).
- `<skill-name>` is kebab-case, no spaces, not already taken.
- Description, if given, is one sentence.

Fail validation → report and stop.

### 2. Read a sibling as a structural model

Read one existing SKILL.md under the same plugin. Default models:

- `mol` → `plugins/mol/skills/note/SKILL.md`
- `mol-agent` → `plugins/mol-agent/skills/check/SKILL.md` (read-only) or `plugins/mol-agent/skills/update/SKILL.md` (writing)
- `mol-plugin` → `plugins/mol-plugin/skills/check/SKILL.md`

Match structure (not content): frontmatter (`name` + `description` + `argument-hint`), Codex adapter directive, H1 `/<plugin>:<skill>` heading, one-paragraph purpose, numbered Procedure, optional Guardrails, optional Idempotency, Output format.

### 3. Resolve the design before authoring

Extract from description + prior conversation:

- **Inputs.** What `$ARGUMENTS` parses as. What it reads from CLAUDE.md / project / siblings.
- **Behavior.** Decisive verbs (probe? generate? gate? delegate? orchestrate?). Branches (success/failure; converge/discard; PROCEED/BLOCK).
- **Outputs.** Files written, agents invoked, user-facing shape, F2 one-line summary.
- **Boundaries.** Read-only vs writing; what it refuses to touch; relation to neighbors (`/mol:spec` vs `/mol:note`, `/mol:fix` vs `/mol:impl`).
- **Invoker class.** **User-invoked** (`disable-model-invocation: true` + `agents/openai.yaml` with `policy.allow_implicit_invocation: false`) when only the human should fire it and **no** sibling will auto-invoke it. **Model-invoked** (omit the flag; optional `allow_implicit_invocation: true`) when the model or another skill must reach it. **Invoker rule:** if skill A auto-invokes skill B, B is model-invoked. See `plugins/mol/rules/design-principles.md` § 2.5. Prefer a thin user entry + model-invoked body only when the same procedure needs both deliberate typing and auto-call (e.g. `/mol:grill` → `/mol:grilling`).

Any unclear → **ask 1–2 targeted questions**. Never write with gaps.

### 4. Author the complete SKILL.md

Frontmatter:

```markdown
---
name: <skill-name>
description: <one or two sentences captured verbatim from the user's intent; mention read-only vs. writes; mention any sibling-skill relationship that defines the boundary>
# user-invoked only (omit both lines for model-invoked):
# disable-model-invocation: true
argument-hint: "<concrete shape — e.g. <arg>, [arg], <arg> [<arg>], <a | b | c>>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.
```

If user-invoked, also write `plugins/<plugin>/skills/<skill-name>/agents/openai.yaml`:

```yaml
interface:
  display_name: "<Title Case Name>"
  short_description: "<one-line human summary>"
policy:
  allow_implicit_invocation: false
```

Body shape (numbered Procedure, concrete steps, no placeholders):

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

Integrity rules:

- **Do not copy another skill's procedure verbatim.** Mirror headings + frontmatter shape; *author* the procedure.
- **Do not create a Codex wrapper or mirror.** One `SKILL.md` is the workflow for both platforms; `skills/CODEX.md` owns runtime translation.
- **Do not invent capabilities the user did not ask for.** Found yourself adding a feature unrequested → stop and ask.

### 5. Reach approval

Show the path + **complete** body. Approval is for redirection ("change step 3 to also do X"), not stub acceptance. No write before approval.

### 6. Apply

Write the file. Report `created plugins/<plugin>/skills/<skill-name>/SKILL.md`.

If user-invoked, also write `plugins/<plugin>/skills/<skill-name>/agents/openai.yaml` with `policy.allow_implicit_invocation: false` (and report that path).

### 7. Register in the plugin README

Append one row to `plugins/<plugin>/README.md`'s skills table. Read the table first; copy column shape:

```
| `/<plugin>:<skill-name>` | <one-sentence purpose, mirroring the frontmatter description's first sentence and matching the voice of neighboring rows> |
```

Insert at bottom of the table, before the next non-table line. Edit nothing else in the README.

### 8. Run `/mol-plugin:check`

Invoke `/mol-plugin:check <plugin>` to confirm structural validation. Errors → fix before exiting.

### 9. Suggest release follow-up

If this skill should ship next release, tell user to run `/mol-plugin:release patch` and `/mol:tag`. Don't run those — release timing is the user's call.

End with one-line F2 summary.

## Guardrails

- **No TODOs in the procedure body.** Distinguishes "scaffold" from "stub".
- **One workflow file.** Never create `codex-skills/` or duplicate an existing skill for compatibility.
- **Do not** create a skill in a non-existent plugin directory; new plugin = bigger decision.
- **Do not** copy another skill's procedure body. Frontmatter shape and headings are fine to mirror.
- **Do not** edit `plugin.json`, `marketplace.json`, or any README section other than the skills table.

## Output format

- Validation result: pass or specific failure.
- Resolved design (4-bullet recap of inputs / behavior / outputs / boundaries).
- Plan: path + complete body preview.
- Application: `created <path>` + one-line README row diff.
- `/mol-plugin:check` verdict.
- Release follow-up prompt: one line, only if applicable.
- Final summary (F2): one line.

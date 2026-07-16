---
name: janitor
description: Review every SKILL.md and agent .md in the marketplace for clarity, orthogonality, and brevity, applying safe rewrites in place and flagging judgement calls as AMBIGUITY. Pairs with `/mol-plugin:check` — that skill audits structure, this skill audits content.
argument-hint: "[<plugin>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol-plugin:janitor — Skill & Agent Content Janitor

Walk every `SKILL.md` and agent `.md`, normalize prose to plain operational language, enforce one clear responsibility per file. Pairs with `/mol-plugin:check` (structural audit).

Scope: no argument → every plugin in `.claude-plugin/marketplace.json`. With plugin name → just that plugin.

## Procedure

### 1. Inventory

Build file list:

- `plugins/<plugin>/skills/<skill>/SKILL.md`
- `plugins/<plugin>/agents/<agent>.md`

Restrict to one plugin if given. Skip files whose YAML frontmatter fails to parse — that belongs to `/mol-plugin:check`.

### 2. Read each file

Extract:

- frontmatter `description` (the contract)
- H1 title + one-paragraph purpose
- Procedure / role-body sections
- Guardrails / Output / Idempotency sections

### 3. Audit per file

Five janitor rules:

- **Single responsibility.** Frontmatter `description` names one job. Flag for split when description lists more than one verb-equivalent ("validate AND fix", "scan AND publish", "review AND apply").
- **Correct placement.** Skills are capability-oriented (verb the user runs: `/mol:fix`, `/mol-plugin:release`). Agents are role-oriented (perspective an orchestrator delegates to: `reviewer`, `scientist`, `janitor`). Flag a skill that reads like a role brief, or an agent that reads like a runnable verb.
- **Actionable language.** Steps and rules use short imperative phrasing — "do X when Y", "refuse when Z", "stop and report". Flag motivational tone, marketing language, vague advice ("be thoughtful", "carefully consider"), abstract terms with no behavioral consequence ("ensure quality", "promote excellence"). Also flag prose paragraphs whose content is *purely enumerable* — three or more parallel facts welded with "and"/"as well as"/"plus" — and propose converting to bullets. Do **not** flag prose carrying causal/conditional logic ("X because Y", "unless Z").
- **Length discipline.** Skills should sit in 200–500 word range. Allowed to exceed *only* when extra prose carries rules that change execution — ordering, branches, recovery, refusal. Flag a skill **both** over 500 words **and** containing actionable-language exclusions. Length alone is not a finding. Trim required is more than language-level (genuinely two skills welded) → AMBIGUITY with `single-responsibility` or `correct-placement`; splitting belongs to author.
- **No duplicate responsibility.** Compare every file's job against every other. Flag the pair when two files claim the same responsibility.

### 4. Audit cross-file

- **Shared rules belong in docs.** Rule repeated verbatim in 3+ files belongs in `plugins/mol/rules/` (or plugin's `docs/`) and should be referenced.
- **Local rules stay local.** Rule applying to exactly one skill stays in that skill.

### 5. Apply safe rewrites

Findings the audit considers safe — language normalization, deleting repeated principles, removing motivational tone, replacing vague phrasing with imperatives — apply minimal patch in place.

Frontmatter `description` and H1 are part of the invocation contract. Tighten language; do not rename.

### 6. Surface judgement calls as AMBIGUITY

Do not act; surface and stop:

- splitting one file into two
- moving a skill to an agent (or vice versa)
- promoting shared content to global docs
- merging two files
- changing a contract surface (`description`, H1, argument-hint)

Author resolves AMBIGUITY entries.

### 7. Verify

After all writes, run `/mol-plugin:check` once. Error introduced by this run → revert offending file with `git checkout -- <path>` and re-flag as AMBIGUITY.

### 8. Output

Severity-sorted findings:

```
<emoji> <path> — <message>
  Rule: <single-responsibility | correct-placement |
         actionable-language | length-discipline |
         no-duplicate-responsibility | shared-rules-in-docs |
         local-rules-stay-local>
  Action: applied | ambiguity
  Diff: <one-line summary if applied>
```

Count summary:

| Plugin       | applied | ambiguity |
|--------------|---------|-----------|
| mol          |         |           |
| mol-plugin   |         |           |

End with one-line F2 summary: files reviewed, lines simplified, overlap removed, ambiguities outstanding.

## Guardrails

- **Do not invent new architecture.** Two files overlap → AMBIGUITY; never merge/rename/move on your own.
- **Do not change contract surfaces.** Frontmatter `description`, `argument-hint`, H1. Tighten language inside; never alter what the skill *is*.
- **Preserve cross-platform markers.** `name` and the one-line `../CODEX.md` directive are required shared-skill structure, not duplicate responsibility.
- **Do not edit non-target files.** READMEs, `plugin.json`, `marketplace.json`, `docs/` are out of scope.
- **Do not touch user-authored prose** in `docs/` or `tests/`. Janitor scope is `skills/` and `agents/` only.
- **Behavior-preserving by contract.** Pass must not change which skills exist, how they're invoked, or what they promise. Rewrite would → revert.

## Idempotency

Re-run on clean tree → zero applied changes. Second pass produces new applied edits → first pass was incomplete; inspect diff before applying again.

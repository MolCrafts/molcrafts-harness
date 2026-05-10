---
description: Review every SKILL.md and agent .md in the marketplace for clarity, orthogonality, and brevity. Normalizes language to plain imperative rules ("do X when Y"), enforces one responsibility per file, separates capability-oriented skills from role-oriented agents, and removes duplicate responsibilities. Applies safe rewrites in place; surfaces judgement calls (splits, moves, merges, promotion of shared rules to docs) as AMBIGUITY without editing. Pairs with /mol-plugin:check — that skill audits structure, this skill audits content. Writes inside plugins/<plugin>/skills/ and plugins/<plugin>/agents/ only.
argument-hint: "[<plugin>]"
---

# /mol-plugin:janitor — Skill & Agent Content Janitor

Walk every `SKILL.md` and agent `.md` in the marketplace, normalize
prose to plain operational language, and enforce one clear
responsibility per file. Pairs with `/mol-plugin:check` (structural
audit) — that skill validates frontmatter and cross-references; this
skill validates *content*.

Scope: with no argument, scans every plugin listed in
`.claude-plugin/marketplace.json`. With a plugin name, scans just
that plugin.

## Procedure

### 1. Inventory

Build the file list:

- `plugins/<plugin>/skills/<skill>/SKILL.md`
- `plugins/<plugin>/agents/<agent>.md`

Restrict to one plugin if a name was given. Skip files whose YAML
frontmatter fails to parse — that class of error belongs to
`/mol-plugin:check`.

### 2. Read each file

Extract these surfaces from every file:

- frontmatter `description` (the contract)
- H1 title and the one-paragraph purpose under it
- Procedure / role-body sections
- Guardrails / Output / Idempotency sections

### 3. Audit per file

Check each file against the five janitor rules:

- **Single responsibility.** The frontmatter `description` must
  name one job. Flag for split when the description lists more
  than one verb-equivalent ("validate AND fix", "scan AND
  publish", "review AND apply").
- **Correct placement.** Skills are capability-oriented — a verb
  the user runs (`/mol:fix`, `/mol-plugin:release`). Agents are
  role-oriented — a perspective an orchestrator delegates to
  (`reviewer`, `scientist`, `janitor`). Flag a skill that reads
  like a role brief, or an agent that reads like a runnable verb.
- **Actionable language.** Steps and rules use short imperative
  phrasing — "do X when Y", "refuse when Z", "stop and report".
  Flag motivational tone, marketing language, vague advice ("be
  thoughtful", "carefully consider"), and abstract terms with no
  behavioral consequence ("ensure quality", "promote excellence").
  Also flag prose paragraphs whose content is *purely
  enumerable* — three or more parallel facts welded together
  with "and" / "as well as" / "plus" — and propose converting
  them to a bulleted list. Do **not** flag prose that carries
  causal or conditional logic ("X because Y", "unless Z") —
  that reasoning would fragment under bullets.
- **Length discipline.** Skills should sit in the 200–500 word
  range. A skill is allowed to exceed that *only* when the extra
  prose carries rules that change execution — ordering
  constraints, branch decisions, recovery paths, refusal
  conditions. Flag a skill that is **both** over 500 words **and**
  contains content matching the actionable-language exclusions
  (motivational tone, repeated principles, background that does
  not gate behavior, examples that don't change the procedure).
  Length alone is not a finding. When the trim required is more
  than language-level — i.e. the skill is genuinely two skills
  welded together — surface as AMBIGUITY with rule
  `single-responsibility` or `correct-placement`; splitting
  belongs to the author.
- **No duplicate responsibility.** Compare every file's job
  against every other file in the marketplace. Flag the pair when
  two files claim the same responsibility.

### 4. Audit cross-file

- **Shared rules belong in docs.** A rule repeated verbatim in
  three or more files belongs in `plugins/mol/rules/` (or the
  plugin's `docs/` folder) and should be referenced, not inlined.
- **Local rules stay local.** A rule that applies to exactly one
  skill must live in that skill, not in shared docs.

### 5. Apply safe rewrites

For each finding the audit considers safe — language normalization,
deleting repeated principles, removing motivational tone, replacing
vague phrasing with imperatives — apply the minimal patch in place.

The frontmatter `description` and the H1 heading are part of the
invocation contract. Tighten their language; do not rename them.

### 6. Surface judgement calls as AMBIGUITY

Do not act on findings that require a judgement call. Surface them
and stop:

- splitting one file into two
- moving a skill to an agent (or vice versa)
- promoting shared content to global docs
- merging two files
- changing a contract surface (`description`, H1, argument-hint)

The author resolves AMBIGUITY entries; this skill does not.

### 7. Verify

After all writes, run `/mol-plugin:check` once. If it reports an
error introduced by this run, revert the offending file with
`git checkout -- <path>` and re-flag the finding as AMBIGUITY.

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

End with a count summary:

| Plugin       | applied | ambiguity |
|--------------|---------|-----------|
| mol          |         |           |
| mol-agent    |         |           |
| mol-plugin   |         |           |

End with a one-line summary (F2): files reviewed, lines
simplified, overlap removed, ambiguities outstanding.

## Guardrails

- **Do not invent new architecture.** When two files overlap, surface
  AMBIGUITY — never merge, rename, or move files on your own
  authority.
- **Do not change contract surfaces.** Frontmatter `description`,
  `argument-hint`, and the H1 heading are how users invoke a skill.
  Tighten language inside; never alter what the skill *is*.
- **Do not edit non-target files.** READMEs, `plugin.json`,
  `marketplace.json`, and `docs/` are out of scope. Those belong to
  `/mol-plugin:release`, `/mol-plugin:check`, and the author.
- **Do not touch user-authored prose** inside `docs/` or `tests/`.
  Janitor scope is `skills/` and `agents/` only.
- **Behavior-preserving by contract.** A janitor pass must not
  change which skills exist, how they are invoked, or what they
  promise. If a rewrite would, revert it.

## Idempotency

Re-running `/mol-plugin:janitor` on a clean tree reports zero
applied changes. If a second pass produces new applied edits, the
first pass was incomplete — inspect the diff before applying again.
